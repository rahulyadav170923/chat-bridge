#!/usr/bin/env python3
from WtlChatAdapters.WtlChatAdapter import WtlChatAdapter
import time
import requests
import telegram
from telegram.error import NetworkError, Unauthorized
from tqdm import tqdm
from urllib.parse import urlparse
from os.path import splitext

class Telegram(WtlChatAdapter):

    def __init__(self, adapter_name,event_emitter, token):
        WtlChatAdapter.__init__(self,adapter_name,event_emitter)
        self.bot = telegram.Bot(token)

        try:
            self.update_id = self.bot.getUpdates()[0].update_id
        except IndexError:
            self.update_id = None

    def download_file(self,file_id):
        file_data = self.bot.getFile(file_id)
        path = urlparse(file_data['file_path']).path
        ext = splitext(path)[1]
        response = requests.get(file_data['file_path'], stream=True)
        out_filename = "/srv/{}{}".format(file_data['file_id'],ext)
        with open(out_filename, "wb") as handle:
            for data in tqdm(response.iter_content()):
                handle.write(data)
        return out_filename

    def run(self):
        while self.running:
            try:
                for update in self.bot.getUpdates(offset=self.update_id, timeout=10):
                    self.update_id = update.update_id + 1

                    if update.message:
                        chat_id = update.message.chat_id
                        message_event = {"adapter_name":self.adapter_name}
                        message_event['channel_id'] = "{}".format(chat_id)
                        message_event['text'] = update.message.text
                        if update.message.document != None:
                            print("Document:")
                            print(self.download_file(update.message.document.file_id))
                        for p in update.message.photo:
                            print("Photo:")
                            print(self.download_file(p.file_id))
                        if update.message.sticker != None:
                            print("Sticker:")
                            print(self.download_file(update.message.sticker.file_id))
                        if update.message.video != None:
                            print("Video:")
                            print(self.download_file(update.message.video.file_id))
                        if update.message.voice != None:
                            print("Voice:")
                            print(self.download_file(update.message.voice.file_id))

                        if update.message.contact != None:
                            print("Contact:")
                            print(update.message.contact.phone_number)
                            print(update.message.contact.first_name)
                            print(update.message.contact.last_name)
                            print(update.message.contact.user_id)
                        if update.message.location != None:
                            print("Location:")
                            print(update.message.location.longitude)
                            print(update.message.location.latitude)

                        if len(update.message.from_user.username) > 0:
                            message_event['from'] = update.message.from_user.username
                        else:
                            message_event['from'] = update.message.from_user.id
                        self.event_emitter.emit('message',message_event)
            except NetworkError:
                time.sleep(1)
            except Unauthorized:
                update_id += 1
            time.sleep(1)
        self.stop()

    def send_msg(self,channel_id,msg):
        self.bot.sendMessage(chat_id=channel_id, text=msg)
