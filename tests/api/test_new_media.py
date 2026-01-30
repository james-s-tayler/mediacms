import uuid

from django.test import Client, TestCase

from files.models import Encoding, Media, Tag, Playlist, PlaylistMedia
from files.tests import create_account

API_V1_LOGIN_URL = '/api/v1/login'


class TestX(TestCase):
    fixtures = ["fixtures/categories.json", "fixtures/encoding_profiles.json"]

    def setUp(self):
        self.password = 'this_is_a_fake_password'

        self.user = create_account(password=self.password)

    def test_file_upload(self):
        client = Client()
        client.login(username=self.user.username, password=self.password)

        # use both ways, form + API to upload a new media file
        # while video transcoding through ffmpeg takes place asynchronously
        # (through celery workers), inside tests ffmpeg runs synchronously
        # because celery is started with setting task_always_eager
        # practically this means that this testing will take some time, but
        # ensures that video transcoding completes well
        with open('fixtures/small_video.mp4', 'rb') as fp:
            client.post('/api/v1/media', {'title': 'small video file test', 'media_file': fp})

        with open('fixtures/test_image.png', 'rb') as fp:
            client.post('/api/v1/media', {'title': 'image file test', 'media_file': fp})

        with open('fixtures/medium_video.mp4', 'rb') as fp:
            client.post('/fu/upload/', {'qqfile': fp, 'qqfilename': 'medium_video.mp4', 'qquuid': str(uuid.uuid4())})

        self.assertEqual(Media.objects.all().count(), 3, "Problem with file upload")
        # by default the portal_workflow is public, so anything uploaded gets public
        self.assertEqual(Media.objects.filter(state='public').count(), 3, "Expected all media to be public, as per the default portal workflow")
        self.assertEqual(Media.objects.filter(media_type='video', encoding_status='success').count(), 2, "Encoding did not finish well")
        self.assertEqual(Media.objects.filter(media_type='video').count(), 2, "Media identification failed")
        self.assertEqual(Media.objects.filter(media_type='image').count(), 1, "Media identification failed")
        self.assertEqual(Media.objects.filter(user=self.user).count(), 3, "User assignment failed")
        medium_video = Media.objects.get(title="medium_video.mp4")
        self.assertEqual(len(medium_video.hls_info), 13, "Problem with HLS info")

        # using the provided EncodeProfiles, these two files should produce 9 Encoding objects.
        # if new EncodeProfiles are added and enabled, this will break!
        self.assertEqual(Encoding.objects.filter(status='success').count(), 10, "Not all video transcodings finished well")

    def test_bulk_import_with_tags_and_playlists(self):
        """Test that bulk import applies tags and playlists to uploaded media"""
        client = Client()
        client.login(username=self.user.username, password=self.password)

        # Create a playlist for testing
        playlist = Playlist.objects.create(title='Test Playlist', user=self.user)

        # Upload a file with bulk tags and playlists
        with open('fixtures/test_image.png', 'rb') as fp:
            response = client.post('/fu/upload/', {
                'qqfile': fp,
                'qqfilename': 'test_bulk_import.png',
                'qquuid': str(uuid.uuid4()),
                'bulk_tags': 'test, import, demo',
                'bulk_playlists': str(playlist.id)
            })

        # Verify the upload was successful
        self.assertEqual(response.status_code, 200)
        
        # Get the uploaded media
        media = Media.objects.get(title='test_bulk_import.png')
        
        # Verify tags were applied
        tags = list(media.tags.all())
        self.assertEqual(len(tags), 3, "Expected 3 tags to be applied")
        tag_titles = [tag.title for tag in tags]
        self.assertIn('test', tag_titles, "Expected 'test' tag")
        self.assertIn('import', tag_titles, "Expected 'import' tag")
        self.assertIn('demo', tag_titles, "Expected 'demo' tag")
        
        # Verify playlist was applied
        playlist_media = PlaylistMedia.objects.filter(media=media, playlist=playlist)
        self.assertEqual(playlist_media.count(), 1, "Expected media to be in playlist")

    def test_bulk_import_with_no_tags_or_playlists(self):
        """Test that upload works normally without bulk import options"""
        client = Client()
        client.login(username=self.user.username, password=self.password)

        # Upload a file without bulk import options
        with open('fixtures/test_image.png', 'rb') as fp:
            response = client.post('/fu/upload/', {
                'qqfile': fp,
                'qqfilename': 'test_normal_import.png',
                'qquuid': str(uuid.uuid4())
            })

        # Verify the upload was successful
        self.assertEqual(response.status_code, 200)
        
        # Get the uploaded media
        media = Media.objects.get(title='test_normal_import.png')
        
        # Verify no tags were applied
        self.assertEqual(media.tags.count(), 0, "Expected no tags to be applied")
        
        # Verify media is not in any playlists
        playlist_media = PlaylistMedia.objects.filter(media=media)
        self.assertEqual(playlist_media.count(), 0, "Expected media to not be in any playlists")
