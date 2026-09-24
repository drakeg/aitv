from django.test import SimpleTestCase

from content.providers import detect_provider


class ProviderDetectionTests(SimpleTestCase):
    def test_roku_channel_is_recognized_as_ad_supported_streaming(self):
        provider = detect_provider('https://therokuchannel.roku.com/details/example')
        self.assertIsNotNone(provider)
        self.assertEqual(provider['provider'], 'The Roku Channel')
        self.assertEqual(provider['access_type'], 'ads')

    def test_prime_video_native_domain_is_recognized(self):
        provider = detect_provider('https://www.primevideo.com/detail/example')
        self.assertIsNotNone(provider)
        self.assertEqual(provider['provider'], 'Prime Video')
        self.assertEqual(provider['access_type'], 'subscription')

    def test_amazon_video_path_is_recognized_without_claiming_all_amazon_links(self):
        provider = detect_provider('https://www.amazon.com/gp/video/detail/example')
        self.assertIsNotNone(provider)
        self.assertEqual(provider['provider'], 'Prime Video')
        self.assertIsNone(detect_provider('https://www.amazon.com/dp/example'))


    def test_major_network_watch_paths_are_recognized(self):
        cases = (
            ('https://abc.com/shows/example', 'ABC'),
            ('https://www.cbs.com/shows/example/', 'CBS'),
            ('https://www.nbc.com/shows/example', 'NBC'),
            ('https://www.fox.com/watch/example/', 'FOX'),
        )
        for url, expected_provider in cases:
            with self.subTest(url=url):
                provider = detect_provider(url)
                self.assertIsNotNone(provider)
                self.assertEqual(provider['provider'], expected_provider)

    def test_major_network_non_watch_paths_are_not_direct_playback(self):
        urls = (
            'https://abc.com/news/example-story',
            'https://www.cbs.com/news/example-story/',
            'https://www.nbc.com/news/example-story',
            'https://www.fox.com/article/example-story/',
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertIsNone(detect_provider(url))
