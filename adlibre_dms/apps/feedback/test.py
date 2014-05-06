"""
Module: Feedback form for DMS Tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2014
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django.core.urlresolvers import reverse
from adlibre.dms.base_test import DMSTestCase


class FeedbackTest(DMSTestCase):
    """Main test for feedback form app"""

    def test_00_opens(self):
        url = reverse('feedback')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_02_opens_for_user(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('feedback')
        response = self.client.get(url)
        self.assertContains(response, 'feedback.js')
        self.assertContains(response, 'id_feedback_body')

    def test_03_post_feedback(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('feedback')
        data = {'feedback_body': 'some test feedback string'}
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('feedback_sent'))

    def test_04_feedback_complete(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('feedback_sent')
        response = self.client.get(url)
        self.assertContains(response, 'Your message was sent successfully')
