import os
import sys
import tkinter as tk
from tkinter import ttk
from threading import Thread

from PIL import Image, ImageTk

from mic import recognize_wheel
from chat import write_history, new_dialogue


class Application(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)

        self.overrideredirect(True)
        self.resizable(False, False)
        self.prepare_img()
        self.create_widgets()
        self.update()

        self.geometry('+{}+{}'.format(self.winfo_screenwidth()-self.winfo_width(),
                               self.winfo_screenheight()-100))
        
        #запуск прослушки микрофона(аппаратной части ассистента)
        # self.run_assistant()
        #запуск функции постоянной проверки значения переменной окружения
        #для обновления виджета, если есть активный диалог с gpt
        self.check_env_vars()

    def create_widgets(self):
        self.assistant_label = ttk.Label(self, image=self.assistant_img_frames[0], background='black')
        self.assistant_label.grid(column=0, row=0, ipadx=0, ipady=0, padx=0, pady=0)
        self.assistant_label.bind("<Button-1>", self.run_assistant)

        self.gpt_label = ttk.Label(self, image=self.gpt_img_frames[0], background='black')
        self.gpt_label.grid(column=1, row=0, ipadx=0, ipady=0, padx=0, pady=0)
        self.gpt_label.bind("<Button-1>", self.run_gpt)

        self.gpt_clear_label = ttk.Label(self, image=self.refresh_img, background='black')
        self.gpt_clear_label.grid(column=2, row=0, ipadx=0, ipady=0, padx=0, pady=0)
        self.gpt_clear_label.bind("<Button-1>", self.clear_gpt)

        self.exit_label = ttk.Label(self, image=self.exit_img, background='black')
        self.exit_label.grid(column=3, row=0, ipadx=0, ipady=0, padx=0, pady=0)
        self.exit_label.bind("<Button-1>", self.exit)
    
    def read_gif_frames(self, gif):
        frames = []
        for frame in range(0, gif.n_frames):
            gif.seek(frame)
            frames.append(ImageTk.PhotoImage(gif.copy()))
        return frames

    def prepare_img(self):
        image = Image.open("images/mic.gif")
        self.assistant_img_frames = self.read_gif_frames(image)

        image = Image.open("images/gpt.gif")
        self.gpt_img_frames = self.read_gif_frames(image)

        self.exit_img = tk.PhotoImage(file="images/exit.png")

        self.refresh_img = tk.PhotoImage(file="images/refresh2.png")
        self.refresh2_img = tk.PhotoImage(file="images/refresh.png")


    def animate_mic(self, frame_index=0):
        self.assistant_label.configure(image=self.assistant_img_frames[frame_index])
        self.wheel_mic_animation = self.after(100, self.animate_mic,
                                              (frame_index + 1) % len(self.assistant_img_frames))

    def animate_gpt(self, frame_index=0):
        self.gpt_label.configure(image=self.gpt_img_frames[frame_index])
        self.wheel_gpt_animation = self.after(100, self.animate_gpt,
                                              (frame_index + 1) % len(self.gpt_img_frames))
        
    def stop_mic_animation(self):
        if self.wheel_mic_animation is not None:
            self.after_cancel(self.wheel_mic_animation)
            self.wheel_mic_animation = None

    def stop_gpt_animation(self):
        if self.wheel_gpt_animation is not None:
            self.after_cancel(self.wheel_gpt_animation)
            self.wheel_gpt_animation = None
        
    def run_assistant(self, event=None):
        if int(os.getenv('MIC')):

            os.environ.update(MIC='0')
            self.stop_mic_animation()
            self.assistant_label['image'] = self.assistant_img_frames[0]

            if int(os.getenv('CHATGPT')):
                os.environ.update(CHATGPT='0')
                self.stop_gpt_animation()
                self.gpt_label['image'] = self.gpt_img_frames[0]
            
        else:
            os.environ.update(MIC='1')
            self.animate_mic()
            p1 = Thread(target=recognize_wheel, daemon=True)
            p1.start()

    def check_env_vars(self):
        '''
        Каждые 5сек проверяем, если появился диалог с gpt,
        то меняем цвет виджета на желтый
        '''
        dialogue_status = os.environ.get('NEW_DIALOGUE')
        if not int(dialogue_status):
            self.gpt_clear_label['image'] = self.refresh2_img

        self.after(5000, self.check_env_vars)

    def run_gpt(self, event):
        
        if int(os.getenv('CHATGPT')):

            os.environ.update(CHATGPT='0')
            self.stop_gpt_animation()
            self.gpt_label['image'] = self.gpt_img_frames[0]

        elif not int(os.getenv('MIC')):
            return
        
        else:
            os.environ.update(CHATGPT='1')
            self.animate_gpt()


    def clear_gpt(self, event):
        new_dialogue()
        os.environ.update(NEW_DIALOGUE='1')
        self.gpt_clear_label['image'] = self.refresh_img


    def exit(self, event):
        write_history()
        sys.exit(0)



