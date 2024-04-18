import os
import sys
import time
import math
import random

import tkinter
from tkinter import ttk
from tkinter import filedialog
import customtkinter as ctk

import pygame
import pygame.mixer as mx
from PIL import Image
from mutagen.mp3 import MP3

from threading import Thread

class Song:
    def __init__(self, song: str):
        self.prev = None
        self.song = song
        self.next = None


class Playlist:

    def __init__(self):
        self.current_song = 0
        self._head = None
        self._tail = None
        self._numSongs = 0

        self.__Queue = []

    def create_playlist(self, playlist):
        for i in playlist:
            song = Song(i)
            if self._head is None:
                self._head = song
                self._tail = self._head

                self._numSongs += 1

            else:
                song.prev = self._tail
                self._tail.next = song
                self._tail = song
                self._numSongs += 1

    def findSong(self, n):
        queue = self.__queue()
        self.current_song = n
        return queue[n]

    def add_song(self, song):
        new_song = Song(song)
        if self._head is None:
            self._head = new_song
            self._tail = self._head
            self._numSongs += 1
        else:
            new_song.prev = self._tail
            self._tail.next = new_song
            self._tail = new_song
            self._numSongs += 1

    def show_playlist(self):
        head = self._head
        playlist = []
        while head is not None:
            playlist.append(head.song)
            head = head.next
        return playlist

    def __queue(self):
        head = self._head
        queue = []
        while head is not None:
            queue.append(head.song)
            head = head.next
        return queue

    def get_nextSong(self, current_song=None):
        try:
            if current_song is None:
                current_song = self.current_song + 1

            assert current_song < self._numSongs
            queue = self.__queue()
            next_song = queue[current_song]
            self.current_song = self.current_song + 1

            return next_song
        except AssertionError:
            return 'End of queue'

    def get_prevSong(self, current_song=None):
        try:
            if current_song is None:
                current_song = self.current_song - 1
            assert current_song >= 0
            queue = self.__queue()

            prev_song = queue[current_song]
            self.current_song = self.current_song + 1

            return prev_song
        except AssertionError:

            return 'End of queue'


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title('SoundBox')
        self.root.geometry('800x480')
        self.root.iconbitmap(resource_path('images/favicon.ico'))
        self.root.resizable(0, 0)

        self.playlist = Playlist()
        self.song_selected = False
        self.added_playlistbox = 0
        self.current_song = 0
        self.song_index = None
        self.stop_threads = False

        mx.init()
        self.musicGUI()

    def musicGUI(self):
        self.cover_pages = [resource_path(os.path.join("images", i)) for i in os.listdir(resource_path('images')) if
                            'cover' in i]
        image = ctk.CTkImage(light_image=Image.open(random.choice(self.cover_pages)), size=(250, 250))
        self.coverpage = ctk.CTkLabel(self.root, text='', image=image)
        self.coverpage.place(relx=0.65, rely=.06)

        self.song_name_label = tkinter.Label(text=" ", font=ctk.CTkFont('Arial', 20, 'bold'), bg='#222222',
                                             fg='white')
        self.song_name_label.place(relx=0.65, rely=.58)

        frame = tkinter.Frame(self.root)
        scrollbar = tkinter.Scrollbar(frame, orient=ctk.VERTICAL)
        self.playlistbox = tkinter.Listbox(frame, width=35, height=20,
                                           yscrollcommand=scrollbar.set,
                                           font=("Arial", 15))

        scrollbar.configure(command=self.playlistbox.yview)
        frame.pack(side=ctk.LEFT, padx=5)
        scrollbar.pack(side=ctk.RIGHT, fill=tkinter.Y)
        self.playlistbox.pack(padx=10, pady=40, side='left')

        openfileBtn = tkinter.Button(self.root, width=10, text="Add song +", font=('Arial Bold', 20,),
                                     command=self.browse_file)
        openfileBtn.place(relx=0.01, rely=0.9)

        folderBtn = tkinter.Button(self.root, width=10, text="Open folder...", font=('Arial Bold', 20,),
                                   command=self.browse_folder)
        folderBtn.place(relx=0.27, rely=0.9)

        self.playImage = ctk.CTkImage(light_image=Image.open(resource_path('images/play.png')), size=(38, 38))
        self.pauseImage = ctk.CTkImage(light_image=Image.open(resource_path('images/pause.png')), size=(38, 38))
        nextImage = ctk.CTkImage(light_image=Image.open(resource_path('images/next-button.png')), size=(35, 35))
        previousImage = ctk.CTkImage(light_image=Image.open(resource_path('images/previous.png')), size=(35, 35))
        volumeImage = ctk.CTkImage(light_image=Image.open(resource_path('images/turn-up-volume.png')), size=(15, 15))
        volumeMuteImage = ctk.CTkImage(light_image=Image.open(resource_path('images/mute.png')), size=(15, 15))

        self.lengthlabel = ctk.CTkLabel(self.root, text='--:--')
        self.lengthlabel.place(relx=0.935, rely=0.64)

        self.currenttimelabel = ctk.CTkLabel(self.root, text='--:--')
        self.currenttimelabel.place(relx=0.62, rely=0.64)

        self.play_button = ctk.CTkButton(master=self.root, width=100, text='', image=self.playImage,
                                         fg_color='transparent',
                                         hover_color='#3a3b3c', command=self.play_song)
        self.play_button.place(relx=0.8, rely=0.75, anchor=tkinter.CENTER)

        next_button = ctk.CTkButton(master=self.root, text='', width=70, image=nextImage, fg_color='transparent',
                                    hover_color='#3a3b3c', command=self.next_song)
        next_button.place(relx=0.92, rely=0.75, anchor=tkinter.CENTER)

        previous_button = ctk.CTkButton(master=self.root, text='', width=70, image=previousImage,
                                        fg_color='transparent',
                                        hover_color='#3a3b3c', command=self.prev_song)
        previous_button.place(relx=0.69, rely=0.75, anchor=tkinter.CENTER)

        volumeMuteicon = ctk.CTkLabel(master=self.root, text='', width=70, image=volumeMuteImage,
                                      fg_color='transparent',
                                      ).place(relx=0.59, rely=0.82)

        volumeIncreaseicon = ctk.CTkLabel(master=self.root, text='', width=70, image=volumeImage,
                                          fg_color='transparent').place(relx=0.93, rely=0.82)
        volume_bar = ctk.CTkSlider(master=self.root, from_=0, to=1, command=self.volume, width=250)
        volume_bar.place(relx=0.8, rely=0.85, anchor=tkinter.CENTER)

        self.duration_bar = ctk.CTkProgressBar(master=self.root, progress_color='#DCDCDC', width=210)
        self.duration_bar.place(relx=0.8, rely=.67, anchor=tkinter.CENTER)

    def add_to_playlist(self, file):

        filename = os.path.basename(file)
        self.playlist.add_song(file)
        self.playlistbox.insert(self.added_playlistbox, filename)
        # time.sleep(0.5)

        # playlist.insert(index, filename_path)
        self.added_playlistbox += 1

    def browse_file(self):
        filename_path = filedialog.askopenfilename()
        if filename_path:
            try:
                self.add_to_playlist(filename_path)
                mx.music.queue(filename_path)
            except pygame.error:
                tkinter.messagebox.showinfo('Something is wrong with the song you are trying to play')

    def browse_folder(self):
        foldername_path = tkinter.filedialog.askdirectory()
        if foldername_path:
            folder = [file for file in os.listdir(foldername_path)]
            i = 0
            added = 0

            popup = tkinter.Toplevel()
            popup.geometry('360x100')
            popup.iconbitmap(resource_path('images/favicon.ico'))
            popup.resizable(0,0)

            a = tkinter.Label(popup, text='', font=('Arial', 15))
            a.place(relx=0.1, rely=0.1)  # grid(row=0, column=0)

            progress = 0
            progress_var = tkinter.DoubleVar()
            progress_bar = ttk.Progressbar(popup, variable=progress_var, length=250, maximum=len(folder))
            progress_bar.place(relx=0.15, rely=0.5)
            popup.pack_slaves()

            while i < len(folder):
                try:
                    file = os.path.join(foldername_path, folder[i])
                    mx.music.queue(file)
                    progress += 1
                    a.configure(text=f'Songs added: {progress}/{len(folder)}')
                    self.add_to_playlist(file)

                    popup.update()
                    # time.sleep(0.1)
                    progress_var.set(progress)
                    added += 1
                    i += 1
                except pygame.error:
                    i += 1

            popup.destroy()




    def song_progress(self):

        song_index = int(self.playlistbox.curselection()[0])
        a = mx.Sound(f'{self.playlist.findSong(song_index)}')
        song_len = a.get_length() * 3
        for i in range(0, math.ceil(song_len)):
            if self.stop_threads:
                break
            time.sleep(.4)
            self.duration_bar.set(mx.music.get_pos() / 1000000)

    def thread(self):
        self.thread1 = Thread(target=self.song_progress)
        self.thread1.daemon = True
        self.thread1.start()

    def play_music(self, song):
        try:
            title = os.path.basename(song)
            self.song_name_label.configure(text=f'Playing: {title}')
            mx.music.stop()
            time.sleep(1)
            self.song_selected = True
            mx.music.load(song)
            mx.music.play()
            self.show_details(song)

            self.thread()

        except pygame.BufferError:
            tkinter.messagebox.showinfo('Something is wrong with the song you are trying to play')

    def pause(self):
        self.paused = True
        mx.music.pause()

    def play_song(self):

        try:
            song_index = int(self.playlistbox.curselection()[0])
            if self.song_selected and not self.check_selected_another(song_index):
                if not self.paused:
                    self.play_button.configure(image=self.playImage)
                    self.pause()
                else:
                    self.play_button.configure(image=self.pauseImage)
                    self.paused = False
                    mx.music.unpause()
            else:
                self.song_index = song_index
                song = self.playlist.findSong(song_index)
                self.paused = False
                self.current_song = song_index
                self.play_button.configure(image=self.pauseImage)
                self.play_music(song)

        except IndexError:
            tkinter.messagebox.showinfo("No song selected", 'Choose Song')

    def check_selected_another(self, song_index):
        if self.song_index == song_index:
            return False
        else:
            return True

    def next_song(self):

        self.current_song += 1
        nextSong = self.playlist.get_nextSong(self.current_song)
        if nextSong == 'End of queue':
            print('No next song')
        else:

            image = ctk.CTkImage(light_image=Image.open(random.choice(self.cover_pages)), size=(250, 250))
            self.coverpage.configure(image=image)
            self.play_music(nextSong)


    def prev_song(self):
        self.current_song -= 1
        prevSong = self.playlist.get_prevSong(self.current_song)

        if prevSong == 'End of queue':
            print('No previous song')
        else:
            image = ctk.CTkImage(light_image=Image.open(random.choice(self.cover_pages)), size=(250, 250))
            self.coverpage.configure(image=image)
            self.play_music(prevSong)

    def volume(self, value):
        mx.music.set_volume(value)

    def start_count(self, length):
        current_time = 0
        while current_time <= length:
            if self.stop_threads:
                break
            if self.paused:
                pass
            else:
                mins, secs = divmod(current_time, 60)
                mins = round(mins)
                secs = round(secs)
                time_format = '{:02d}:{:02d}'.format(mins, secs)
                self.currenttimelabel.configure(text=time_format)
                time.sleep(1)
                current_time += 1

    def show_details(self, play_song):
        file_data = os.path.splitext(play_song)

        if file_data[1] == '.mp3':
            audio = MP3(play_song)
            total_length = audio.info.length
        else:
            a = mx.Sound(play_song)
            total_length = a.get_length()

        mins, secs = divmod(total_length, 60)
        mins = round(mins)
        secs = round(secs)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        self.lengthlabel.configure(text=timeformat)
        self.thread2 = Thread(target=self.start_count, args=(total_length,))
        self.thread2.daemon = True
        self.thread2.start()

    def on_closing(self):
        self.stop_threads = True
        mx.music.stop()


def musicApp():
    app = ctk.CTk()
    musicplayer = MusicPlayer(app)
    app.mainloop()
    musicplayer.on_closing()


if __name__ == '__main__':
    print('Starting App.....')
    musicApp()



