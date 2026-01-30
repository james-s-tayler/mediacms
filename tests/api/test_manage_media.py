from django.core.files import File
from django.test import Client, TestCase

from files.models import Media
from files.tests import create_account


class TestManageMediaAPI(TestCase):
    """Tests for the manage media API endpoint (/manage/media/)"""
    fixtures = ["fixtures/categories.json", "fixtures/encoding_profiles.json"]

    def setUp(self):
        self.client = Client()
        self.password = 'test_password123'
        
        # Create an editor user (needed for manage media access)
        self.editor_user = create_account(
            username='editor_user',
            password=self.password,
            is_editor=True
        )
        
        # Create a regular user (should not have access)
        self.regular_user = create_account(
            username='regular_user',
            password=self.password
        )
        
        # Create test media items
        with open('fixtures/test_image2.jpg', "rb") as f:
            myfile = File(f)
            
            # Media with no reports
            self.media_no_reports = Media.objects.create(
                title="Not Reported Media",
                description="Test Description",
                user=self.editor_user,
                state="public",
                encoding_status="success",
                is_reviewed=True,
                reported_times=0,
                media_file=myfile
            )
        
        with open('fixtures/test_image2.jpg', "rb") as f:
            myfile = File(f)
            
            # Media with reports
            self.media_with_reports = Media.objects.create(
                title="Reported Media",
                description="Test Description",
                user=self.editor_user,
                state="public",
                encoding_status="success",
                is_reviewed=True,
                reported_times=3,
                media_file=myfile
            )
        
        with open('fixtures/test_image2.jpg', "rb") as f:
            myfile = File(f)
            
            # Another media with reports
            self.media_with_reports_2 = Media.objects.create(
                title="Another Reported Media",
                description="Test Description",
                user=self.editor_user,
                state="private",
                encoding_status="success",
                is_reviewed=False,
                reported_times=1,
                media_file=myfile
            )

    def test_manage_media_requires_editor_permission(self):
        """Test that the manage media endpoint requires editor permission"""
        # Try without authentication
        response = self.client.get('/manage/media/')
        self.assertEqual(response.status_code, 401, "Unauthenticated request should return 401")
        
        # Try with regular user
        self.client.login(username='regular_user', password=self.password)
        response = self.client.get('/manage/media/')
        self.assertEqual(response.status_code, 403, "Regular user should not have access")
        
        # Should work with editor user
        self.client.login(username='editor_user', password=self.password)
        response = self.client.get('/manage/media/')
        self.assertEqual(response.status_code, 200, "Editor user should have access")

    def test_filter_by_reported_true(self):
        """Test filtering by reported=true returns only reported media"""
        self.client.login(username='editor_user', password=self.password)
        
        response = self.client.get('/manage/media/', {'reported': 'true'})
        
        self.assertEqual(response.status_code, 200, "Request should succeed")
        self.assertIn('results', response.data, "Response should contain results")
        
        # Check that only reported media is returned
        media_titles = [item['title'] for item in response.data['results']]
        self.assertIn(self.media_with_reports.title, media_titles, 
                     "Reported media should be in results")
        self.assertIn(self.media_with_reports_2.title, media_titles, 
                     "Another reported media should be in results")
        self.assertNotIn(self.media_no_reports.title, media_titles, 
                        "Non-reported media should not be in results")
        
        # Verify all results have reported_times > 0
        for item in response.data['results']:
            self.assertGreater(item['reported_times'], 0, 
                             "All filtered results should have reported_times > 0")

    def test_filter_by_reported_false(self):
        """Test filtering by reported=false returns only non-reported media"""
        self.client.login(username='editor_user', password=self.password)
        
        response = self.client.get('/manage/media/', {'reported': 'false'})
        
        self.assertEqual(response.status_code, 200, "Request should succeed")
        self.assertIn('results', response.data, "Response should contain results")
        
        # Check that only non-reported media is returned
        media_titles = [item['title'] for item in response.data['results']]
        self.assertIn(self.media_no_reports.title, media_titles, 
                     "Non-reported media should be in results")
        self.assertNotIn(self.media_with_reports.title, media_titles, 
                        "Reported media should not be in results")
        self.assertNotIn(self.media_with_reports_2.title, media_titles, 
                        "Another reported media should not be in results")
        
        # Verify all results have reported_times = 0
        for item in response.data['results']:
            self.assertEqual(item['reported_times'], 0, 
                           "All filtered results should have reported_times = 0")

    def test_filter_by_reported_all(self):
        """Test filtering by reported=all or no filter returns all media"""
        self.client.login(username='editor_user', password=self.password)
        
        # Test with reported=all
        response = self.client.get('/manage/media/', {'reported': 'all'})
        self.assertEqual(response.status_code, 200, "Request should succeed")
        
        media_titles = [item['title'] for item in response.data['results']]
        self.assertIn(self.media_with_reports.title, media_titles)
        self.assertIn(self.media_no_reports.title, media_titles)
        
        # Test without reported parameter (should default to all)
        response = self.client.get('/manage/media/')
        self.assertEqual(response.status_code, 200, "Request should succeed")
        
        media_titles = [item['title'] for item in response.data['results']]
        self.assertIn(self.media_with_reports.title, media_titles)
        self.assertIn(self.media_no_reports.title, media_titles)

    def test_filter_reported_combined_with_other_filters(self):
        """Test that reported filter works together with other filters"""
        self.client.login(username='editor_user', password=self.password)
        
        # Filter by reported=true and state=private
        response = self.client.get('/manage/media/', {
            'reported': 'true',
            'state': 'private'
        })
        
        self.assertEqual(response.status_code, 200, "Request should succeed")
        
        # Should only return private reported media
        media_titles = [item['title'] for item in response.data['results']]
        self.assertIn(self.media_with_reports_2.title, media_titles, 
                     "Private reported media should be in results")
        self.assertNotIn(self.media_with_reports.title, media_titles, 
                        "Public reported media should not be in results")
        self.assertNotIn(self.media_no_reports.title, media_titles, 
                        "Non-reported media should not be in results")

    def test_sort_by_reported_times(self):
        """Test that sorting by reported_times works correctly"""
        self.client.login(username='editor_user', password=self.password)
        
        # Sort by reported_times descending (default)
        response = self.client.get('/manage/media/', {
            'sort_by': 'reported_times',
            'ordering': 'desc'
        })
        
        self.assertEqual(response.status_code, 200, "Request should succeed")
        
        results = response.data['results']
        if len(results) >= 2:
            # Verify descending order
            for i in range(len(results) - 1):
                self.assertGreaterEqual(
                    results[i]['reported_times'],
                    results[i + 1]['reported_times'],
                    "Results should be sorted by reported_times in descending order"
                )
        
        # Sort by reported_times ascending
        response = self.client.get('/manage/media/', {
            'sort_by': 'reported_times',
            'ordering': 'asc'
        })
        
        self.assertEqual(response.status_code, 200, "Request should succeed")
        
        results = response.data['results']
        if len(results) >= 2:
            # Verify ascending order
            for i in range(len(results) - 1):
                self.assertLessEqual(
                    results[i]['reported_times'],
                    results[i + 1]['reported_times'],
                    "Results should be sorted by reported_times in ascending order"
                )
