# -*- coding: utf-8 -*-
import os
import shutil

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.http import JsonResponse
from django.views import generic

from files.helpers import rm_file, get_alphanumeric_only
from files.methods import user_allowed_to_upload
from files.models import Media, Tag, Playlist, PlaylistMedia

from .fineuploader import ChunkedFineUploader
from .forms import FineUploaderUploadForm, FineUploaderUploadSuccessForm


class FineUploaderView(generic.FormView):
    http_method_names = ("post",)
    form_class_upload = FineUploaderUploadForm
    form_class_upload_success = FineUploaderUploadSuccessForm

    @property
    def concurrent(self):
        return settings.CONCURRENT_UPLOADS

    @property
    def chunks_done(self):
        return self.chunks_done_param_name in self.request.GET

    @property
    def chunks_done_param_name(self):
        return settings.CHUNKS_DONE_PARAM_NAME

    def make_response(self, data, **kwargs):
        return JsonResponse(data, **kwargs)

    def get_form(self, form_class=None):
        if self.chunks_done:
            form_class = self.form_class_upload_success
        else:
            form_class = self.form_class_upload
        return form_class(**self.get_form_kwargs())

    def dispatch(self, request, *args, **kwargs):
        if not user_allowed_to_upload(request):
            raise PermissionDenied  # HTTP 403
        return super(FineUploaderView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        self.upload = ChunkedFineUploader(form.cleaned_data, self.concurrent)
        if self.upload.concurrent and self.chunks_done:
            try:
                self.upload.combine_chunks()
            except FileNotFoundError:
                data = {"success": False, "error": "Error with File Uploading"}
                return self.make_response(data, status=400)
        elif self.upload.total_parts == 1:
            self.upload.save()
        else:
            self.upload.save()
            return self.make_response({"success": True})
        # create media!
        media_file = os.path.join(settings.MEDIA_ROOT, self.upload.real_path)
        with open(media_file, "rb") as f:
            myfile = File(f)
            new = Media.objects.create(media_file=myfile, user=self.request.user, title=self.upload.original_filename)
        
        # Apply bulk tags if provided
        bulk_tags = form.cleaned_data.get('bulk_tags', '').strip()
        if bulk_tags:
            tag_titles = [t.strip() for t in bulk_tags.split(',') if t.strip()]
            for tag_title in tag_titles:
                # Sanitize and truncate tag title (max 99 chars before get_or_create)
                sanitized_title = get_alphanumeric_only(tag_title)[:99]
                if sanitized_title:
                    tag, created = Tag.objects.get_or_create(
                        title=sanitized_title,
                        defaults={'user': self.request.user}
                    )
                    new.tags.add(tag)
        
        # Apply bulk playlists if provided
        bulk_playlists = form.cleaned_data.get('bulk_playlists', '').strip()
        if bulk_playlists:
            playlist_ids = [p.strip() for p in bulk_playlists.split(',') if p.strip()]
            for playlist_id in playlist_ids:
                try:
                    playlist = Playlist.objects.get(id=int(playlist_id), user=self.request.user)
                    # Use aggregate Max to avoid race conditions
                    from django.db.models import Max
                    max_result = PlaylistMedia.objects.filter(playlist=playlist).aggregate(Max('ordering'))
                    max_ordering = max_result['ordering__max'] or 0
                    PlaylistMedia.objects.create(
                        playlist=playlist,
                        media=new,
                        ordering=max_ordering + 1
                    )
                except (ValueError, Playlist.DoesNotExist):
                    # Skip invalid playlist IDs or playlists not owned by user
                    pass
        
        rm_file(media_file)
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, self.upload.file_path))
        return self.make_response({"success": True, "media_url": new.get_absolute_url()})

    def form_invalid(self, form):
        data = {"success": False, "error": "%s" % repr(form.errors)}
        return self.make_response(data, status=400)
