import datetime
import logging
import os
import re
import shutil
import subprocess

import librosa
import soundfile as sf
from matplotlib import pyplot
from mtcnn.mtcnn import MTCNN
from pymongo import MongoClient
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class Tel_bot:
    def __init__(self, db, token):
        self.__db = db
        self.__audio_collection = db['audio_collection']
        self.__image_collection = db['image_collection']
        self.__token = token

    def start(self, update, context):
        update.message.reply_text("Hello, user.")
        print(update.message.chat.id)

        print(update.message.chat.username)
        print(update.message.chat.type)

    def help_command(self, update, context):
        update.message.reply_text("This bot can convert audio and can recognize face on the photo.")

    def echo(self, update, context):
        update.message.reply_text(update.message.text)
        update.message.reply_text("Хватит радовать меня, кожаный ублюдок (_|_) 😌😡")
        print(update.message.text)

    def audio_handler(self, update, context):
        file = update.message.voice.get_file()
        downloaded = file.download()
        path = "./dir_for_audio"
        output = str(downloaded)
        output = re.findall(r'\d+', output)
        id = self.post_in_db(self.__audio_collection, update.message.chat,
                             "./dir_for_audio/{}".format(
                                 '{0}_audio_message_{1}.wav'.format(update.message.chat.id, output[0])))
        print(id)
        self.change_sr(downloaded, '{0}_audio_message_{1}.wav'.format(update.message.chat.id, output[0]))
        os.remove(downloaded)
        shutil.move('{0}_audio_message_{1}.wav'.format(update.message.chat.id, output[0]), path)

    def change_sr(self, src_filename, dest_filename, sample_rate=16000):
        process = subprocess.run(['ffmpeg', '-i', src_filename, dest_filename])
        if process.returncode != 0:
            raise Exception("Smth went wrong")

        x, sr = librosa.load(dest_filename, sr=sample_rate)
        sf.write(dest_filename, x, sr)

    def image_handler(self, update, context):
        file = update.message.photo[-1].get_file()
        path = './dir_for_image'
        downloaded = file.download()
        os.rename(downloaded, "{0}_{1}".format(update.message.chat.id, downloaded))
        photo = "{0}_{1}".format(update.message.chat.id, downloaded)

        if self.detect_face(str(photo)):
            update.message.reply_text("На фотографии обнаружено лицо.")
            id = self.post_in_db(self.__image_collection, update.message.chat.id, "./dir_for_image/{}".format(photo))
            print(id)
            shutil.move(str(photo), path)
        else:
            update.message.reply_text("На фотографии не обнаружено лицо.")
            os.remove(photo)

    def post_in_db(self, db_collection, chat_id, path):
        newpost = {
            "chat_id": "{}".format(chat_id),
            "file_path": "{}".format(path),
            "date": datetime.datetime.utcnow()
        }
        inserted_id = db_collection.insert_one(newpost).inserted_id
        return inserted_id

    def detect_face(self, image):
        pixels = pyplot.imread(image)
        detector = MTCNN()
        face = detector.detect_faces(pixels)
        if len(face) == 0:
            result = False
        else:
            result = True
        return result

    def main(self):
        updater = Updater("{}".format(self.__token), use_context=True)

        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", self.start))
        dp.add_handler(CommandHandler("help", self.help_command))

        dp.add_handler(MessageHandler(Filters.voice, self.audio_handler))
        dp.add_handler(MessageHandler(Filters.text & ~Filters.command, self.echo))
        dp.add_handler(MessageHandler(Filters.photo, self.image_handler))

        updater.start_polling()

        updater.idle()


if __name__ == '__main__':
    # path = './photo_set'
    # images = get_images(path)

    # filename = 'test1.jpg'
    # load image from file
    # print(detect_face(filename))
    # display faces on the original image
    # cv2.destroyAllWindows()

    # face_recognizer.train(images, np.array(labels))
    # print(detect_face('file_32.jpg'))
    # print(detect_face('file_33.jpg'))
    print("Hello world!!")
    client = MongoClient("mongodb://127.0.0.1:27017")
    db = client['bot_database']
    token = "1304239271:AAFCLaZF3PcNFLcuoMdnl5NmHKrXl5FfGj8"
    tel_bot = Tel_bot(db, token)
    tel_bot.main()
