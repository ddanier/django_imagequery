# -*- coding: utf-8 -*-
import os
import shutil
from django.test import TestCase
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models

from imagequery.query import ImageQuery


class ImageModel(models.Model):
        name = models.CharField(max_length=50)
        image = models.ImageField(upload_to='test')

        def __unicode__(self):
                return self.name

        @models.permalink
        def get_absolute_url(self):
                return '-detail', (self.slug,), {}


class ImageQueryTest(TestCase):
	def setUp(self):
		self.sample_dir = os.path.join(os.path.dirname(__file__), 'sampleimages')
		import tempfile
		self.tmp_dir = tempfile.mkdtemp()
		self.media_root = settings.MEDIA_ROOT
		settings.MEDIA_ROOT = self.tmp_dir
		self.tmpstorage_dir = tempfile.mkdtemp()
                self.tmpstorage = FileSystemStorage(location=self.tmpstorage_dir)

	def tearDown(self):
		settings.MEDIA_ROOT = self.media_root

	def sample(self, path):
		return os.path.join(self.sample_dir, path)
	def tmp(self, path):
		return os.path.join(self.tmp_dir, path)
	def compare(self, im1, im2):
		import hashlib
		f1hash = hashlib.md5()
		f1hash.update(file(im1).read())
		f2hash = hashlib.md5()
		f2hash.update(file(im2).read())
		return f1hash.hexdigest() == f2hash.hexdigest()

	def test_load_simple_filename(self):
		iq = ImageQuery(self.sample('django_colors.jpg'))
		iq.grayscale().save(self.tmp('test.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/django_colors_gray.jpg')))

        def test_load_open_image_file(self):
		import Image
		iq = ImageQuery(Image.open(self.sample('django_colors.jpg')))
		iq.grayscale().save(self.tmp('test.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/django_colors_gray.jpg')))

        def test_load_blank_image(self):
		blank = ImageQuery(x=100,y=100,color=(250,200,150,100))
		blank.save(self.tmp('test.png'))
		self.assert_(self.compare(self.tmp('test.png'), self.sample('results/blank_100x100_250,200,150,100.png')))

        def test_load_model_field(self):
                instance = ImageModel.objects.create(name='Hi', image=self.sample('django_colors.jpg'))
                instance = ImageModel.objects.get(pk=instance.pk)
                iq = ImageQuery(instance.image)
		iq.grayscale().save(self.tmp('test.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/django_colors_gray.jpg')))

        def test_load_from_custom_storage(self):
                shutil.copyfile(self.sample('django_colors.jpg'), os.path.join(self.tmpstorage_dir, 'customstorage.jpg'))
                # load from custom tmp storage
                iq = ImageQuery('customstorage.jpg', storage=self.tmpstorage)
		iq.grayscale().save('save.jpg')
		self.assert_(self.compare(os.path.join(self.tmpstorage_dir, 'save.jpg'), self.sample('results/django_colors_gray.jpg')))

	def testOperations(self):
		dj = ImageQuery(self.sample('django_colors.jpg'))
		tux = ImageQuery(self.sample('tux_transparent.png'))
		lynx = ImageQuery(self.sample('lynx_kitten.jpg'))

		dj.grayscale().save(self.tmp('test.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/django_colors_gray.jpg')))

		dj.paste(tux, 'center', 'bottom').save(self.tmp('test.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/django_colors_with_tux_center_bottom.jpg')))

		lynx.mirror().flip().invert().resize(400,300).save(self.tmp('test.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/lynx_kitten_mirror_flip_invert_resize_400_300.jpg')))

		lynx.fit(400,160).save(self.tmp('test.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/lynx_fit_400_160.jpg')))

		tux_blank = tux.blank(color='#000088').save(self.tmp('test.png'))
		self.assert_(self.compare(self.tmp('test.png'), self.sample('results/tux_blank_000088.png')))
		self.assertEqual(tux.size(), tux_blank.size())

		lynx.resize(400).save(self.tmp('test.jpg'))
		lynx.resize(400).sharpness(3).save(self.tmp('test2.jpg'))
		lynx.resize(400).sharpness(-1).save(self.tmp('test3.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/lynx_resize_400.jpg')))
		self.assert_(self.compare(self.tmp('test2.jpg'), self.sample('results/lynx_resize_400_sharpness_3.jpg')))
		self.assert_(self.compare(self.tmp('test3.jpg'), self.sample('results/lynx_resize_400_sharpness_-1.jpg')))
		self.assert_(not self.compare(self.tmp('test.jpg'), self.tmp('test2.jpg')))

		dj.text('Django ImageQuery', 'center', 10, self.sample('../samplefonts/Vera.ttf'), 20, '#000000').save(self.tmp('test.jpg'))
		self.assert_(self.compare(self.tmp('test.jpg'), self.sample('results/django_colors_text_center_10.jpg')))

		self.assertEqual(dj.mimetype(), 'image/jpeg')
		self.assertEqual(tux.mimetype(), 'image/png')

	def testHashCalculation(self):
		dj = ImageQuery(self.sample('django_colors.jpg'))
		self.assertEqual(dj._name(), self.sample('django_colors.jpg'))
		dj1 = dj.scale(100,100)
		self.assertNotEqual(dj1._name(), dj._name())
		dj2 = ImageQuery(self.sample('django_colors.jpg')).scale(100,100)
		self.assertEqual(dj1._name(), dj2._name())
		self.assertNotEqual(dj._name(), dj2._name())
		dj3 = dj.scale(101,101)
		self.assertNotEqual(dj1._name(), dj3._name())
