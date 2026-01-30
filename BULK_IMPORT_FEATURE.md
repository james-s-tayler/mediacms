# Bulk Import Feature Documentation

## Overview
This feature allows users to specify tags and playlists that should be automatically applied to all media files being uploaded. This saves time when uploading multiple files that should share the same tags and be added to the same playlists.

## User Interface

### Location
The bulk import options appear on the media upload page (`/add/`), above the file upload area.

### Components

1. **Bulk Import Options Section**
   - A light gray container with padding
   - Contains explanatory text: "Apply tags and playlists to all uploaded media"

2. **Tags Input Field**
   - Label: "Tags (comma-separated)"
   - Placeholder: "e.g. tutorial, python, education"
   - Accepts comma-separated tag names
   - Help text: "These tags will be added to all uploaded media"

3. **Playlists Selector**
   - Label: "Playlists"
   - Multi-select dropdown showing user's existing playlists
   - Dynamically loads playlists via API when page loads
   - Help text: "Hold Ctrl/Cmd to select multiple playlists"
   - Shows "Loading playlists..." while fetching
   - Shows "No playlists available. Create one first." if user has no playlists

## Backend Implementation

### Modified Files

1. **templates/cms/add-media.html**
   - Added UI section for bulk import options
   - Added JavaScript to load user's playlists
   - Modified FineUploader configuration to pass bulk_tags and bulk_playlists parameters

2. **uploader/forms.py**
   - Added `bulk_tags` CharField (optional) to FineUploaderUploadForm
   - Added `bulk_playlists` CharField (optional) to FineUploaderUploadForm
   - Added same fields to FineUploaderUploadSuccessForm

3. **uploader/views.py**
   - Imported required models: Tag, Playlist, PlaylistMedia
   - Imported helper function: get_alphanumeric_only
   - Added tag processing logic:
     - Splits comma-separated tags
     - Sanitizes each tag using get_alphanumeric_only
     - Truncates to 99 characters (matching existing behavior)
     - Creates tags if they don't exist (get_or_create)
     - Associates tags with uploaded media
   - Added playlist processing logic:
     - Validates playlist IDs
     - Ensures user owns the playlists
     - Uses Max aggregation to determine proper ordering (avoiding race conditions)
     - Adds media to playlists via PlaylistMedia junction table

### API Parameters

The upload endpoint (`/fu/upload/`) now accepts two additional optional parameters:

- `bulk_tags` (string): Comma-separated list of tag names (e.g., "tutorial,python,education")
- `bulk_playlists` (string): Comma-separated list of playlist IDs (e.g., "1,3,5")

## Usage Example

1. User navigates to `/add/`
2. User enters tags in the tags input: "tutorial, python, coding"
3. User selects playlists from the dropdown (e.g., "Python Tutorials" and "Beginner Content")
4. User uploads one or more files
5. All uploaded files automatically receive:
   - Tags: tutorial, python, coding (sanitized to lowercase alphanumeric)
   - Added to: "Python Tutorials" and "Beginner Content" playlists

## Technical Details

### Tag Processing
- Tags are sanitized using `get_alphanumeric_only()` which:
  - Removes all non-alphanumeric characters
  - Converts to lowercase
  - Ensures consistency with existing tag handling
- Maximum tag length: 99 characters (before sanitization)
- Duplicate tags are handled by get_or_create
- Invalid/empty tags are skipped

### Playlist Processing
- Only playlists owned by the uploading user can be selected
- Media is added to playlists with proper ordering
- Uses Django's Max aggregation to avoid race conditions
- Invalid playlist IDs are silently skipped
- Maintains backward compatibility (works without bulk options)

### Security Considerations
- User authentication required (inherited from existing upload permissions)
- Playlist ownership validated server-side
- No code injection risks (input sanitized)
- CodeQL security scan: 0 alerts

## Testing

Added comprehensive tests in `tests/api/test_new_media.py`:

1. **test_bulk_import_with_tags_and_playlists**
   - Verifies tags are correctly applied
   - Verifies playlists are correctly associated
   - Checks proper sanitization of tag names

2. **test_bulk_import_with_no_tags_or_playlists**
   - Ensures backward compatibility
   - Verifies normal uploads work without bulk options

## Backward Compatibility

The feature is fully backward compatible:
- Existing uploads work without any changes
- Optional parameters default to empty strings
- No database migrations required
- No changes to existing API behavior

## Future Enhancements

Possible improvements for future versions:
- Tag autocomplete/suggestions
- Ability to create new playlists from the upload page
- Batch edit of bulk options for already-queued uploads
- Save bulk option presets for frequent upload patterns
- Visual confirmation of applied tags/playlists after upload
