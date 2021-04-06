import random
import numpy as np
from scipy import ndimage
from scipy.ndimage.filters import gaussian_filter
from scipy.ndimage.interpolation import map_coordinates
from skimage.transform import resize


# TODO: elastic transform doesn't work yet with the 26 layered mask/instance mem/weight
def elastic_transform(image, mask, ins, weight, alpha, sigma, random_state=None):
    """Elastic deformation of images as described in [Simard2003]_.
    .. [Simard2003] Simard, Steinkraus and Platt, "Best Practices for
       Convolutional Neural Networks applied to Visual Document Analysis", in
       Proc. of the International Conference on Document Analysis and
       Recognition, 2003.
       
       Modified from: https://gist.github.com/erniejunior/601cdf56d2b424757de5
    """
    if random_state is None:
        random_state = np.random.RandomState(None)

    shape = image.shape
    dx = gaussian_filter((random_state.rand(*shape) * 2 - 1), sigma, mode="constant", cval=0) * alpha
    dy = gaussian_filter((random_state.rand(*shape) * 2 - 1), sigma, mode="constant", cval=0) * alpha
    dz = gaussian_filter((random_state.rand(*shape) * 2 - 1), sigma, mode="constant", cval=0) * alpha

    x, y, z = np.meshgrid(np.arange(shape[0]), np.arange(shape[1]), np.arange(shape[2]))
    indices = np.reshape(y + dy, (-1, 1)), np.reshape(x + dx, (-1, 1)), np.reshape(z + dz, (-1, 1))
    indices_layered = np.reshape(y + dy, (-1, 1)), np.reshape(x + dx, (-1, 1))

    distorted_image = map_coordinates(image, indices, order=1, mode='reflect')
    layers = np.shape(mask)[2]
    distorted_mask = np.zeros(np.shape(mask))
    distorted_ins = np.zeros(np.shape(ins))
    distorted_weight = np.zeros(np.shape(weight))
    for layer in range(layers):
        distorted_mask[:,:,layer] = map_coordinates(mask[:,:,layer], indices_layered, order=1, mode='reflect')
        distorted_ins[:,:,layer] = map_coordinates(ins[:,:,layer], indices_layered, order=1, mode='reflect')
        distorted_weight[:,:,layer] = map_coordinates(weight[:,:,layer], indices_layered, order=1, mode='reflect')

    return distored_image.reshape(image.shape), distored_mask.reshape(mask.shape), distorted_ins.reshape(
        ins.shape), distorted_weight.reshape(weight.shape)


def gaussian_blur(image):
    return gaussian_filter(image, sigma=1)


def gaussian_noise(image):
    mean = 0
    var = 0.1
    sigma = var ** 0.5
    gauss = 50 * np.random.normal(mean, sigma, image.shape)
    gauss = gauss.reshape(image.shape)
    return image + gauss


def rotate(image, ins, gt, weight):
    degree = [90, 180, 270]
    d = degree[random.randint(0, len(degree) - 1)]
    rotate_img = ndimage.rotate(image, d, (1, 2), reshape=False)
    rotate_ins = ndimage.rotate(ins, d, (1, 2), reshape=False)
    rotate_gt = ndimage.rotate(gt, d, (1, 2), reshape=False)
    rotate_weight = ndimage.rotate(weight, d, (1, 2), reshape=False)
    return rotate_img, rotate_ins, rotate_gt, rotate_weight


def random_crop(image, ins, gt, weight, depth=80):
    out_shape = np.shape(image)  # (128, 128, 3)  # originally 128x128x3
    out_shape_layered = np.shape(ins)
    start = random.randint(0, image.shape[0] - depth - 1)

    image = crop_z(image, start, start + depth)
    ins = ins[start:start+depth,:,:]
    gt = gt[start:start+depth,:,:]
    weight = weight[start:start+depth,:,:]

    crop_img = resize(image, out_shape, order=1, preserve_range=True)
    crop_ins = resize(ins, out_shape_layered, order=0, preserve_range=True)
    crop_gt = resize(gt, out_shape_layered, order=0, preserve_range=True)
    crop_weight = resize(weight, out_shape_layered, order=1, preserve_range=True)

    return crop_img, crop_ins, crop_gt, crop_weight


def crop_z(arr, start, end):
    return arr[start:end]
