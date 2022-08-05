from rabbitmq.rabbitmq import Creator
from PIL import Image

import numpy as np

import yadisk
import random
import pickle
import yaml
import cv2
import os


try:
    with open(os.path.join(os.path.dirname(os.getcwd()), os.path.join("config", "config.yaml"))) as file:
        config = yaml.safe_load(file)
except Exception as err:
    print(err)


def main():
    """функция запуска"""
    image = get_image()
    send_rabbitmq(image)
    read_rabbitmq(os.path.dirname(image))


def get_image():
    """Функция получения рандомного сообщения"""
    images_path = os.path.join(os.path.dirname(os.getcwd()), "media", "images")
    img = random.choice(os.listdir(images_path))
    return os.path.join(images_path, img)


def send_rabbitmq(image):
    """Функция, отправляющая изображение в очередь rabbitmq"""
    choices = ["gray", "resize"]
    data = {"img": image_to_array(image), "command": random.choice(choices)}
    pickle_data = pickle.dumps(data)
    rabbitmq_creator.send_data({"data": pickle_data, "queue": "image_move"})


def read_rabbitmq(file_path):
    """Функция получения и отправки файла на диск"""
    data = rabbitmq_creator.get_data()
    data = pickle.loads(data["data"])
    img = pickle_to_image(data["img"], file_path)
    if data["command"] == "gray":
        make_gray(img)
    else:
        resize_image(img)
    upload_to_disk(img)


def upload_to_disk(filename):
    """Функция загрузки фото на яндекс диск"""
    y = yadisk.YaDisk(config["YANDEX"]["ID"], config["YANDEX"]["SECRET"], config["YANDEX"]["TOKEN"])
    with open(filename, "rb") as f:
        y.upload(path_or_file=f, dst_path=config["YANDEX"]["DIR"] + filename.split("/")[-1])
    os.remove(filename)


def image_to_array(image):
    """Функция преобразования фото в массив"""
    img = Image.open(image)
    img_array = np.asarray(img)
    return img_array


def make_gray(image):
    """Функция преобразования цвета ищображения в серый"""
    img = cv2.imread(image)
    grayscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(image, grayscale)


def resize_image(image):
    """Функция изменения размера изображения"""
    img = cv2.imread(image)
    scale_percent = 60
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    output = cv2.resize(img, dsize=dim)
    cv2.imwrite(image, output)


def generate_filename():
    """Функция создания рандомного имени файла"""
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    file_name = ""
    for i in range(10):
        file_name += alphabet[random.randint(0, len(alphabet)-1)]
    return file_name + ".png"


def pickle_to_image(data, filepath):
    """Функция создания изображения из байтов"""
    filename = os.path.join(filepath, generate_filename())
    img = Image.fromarray(data)
    img.save(filename)
    return filename


if __name__ == "__main__":
    rabbitmq_creator = Creator(config['RABBITMQ'])
    rabbitmq_creator.start()
    main()
