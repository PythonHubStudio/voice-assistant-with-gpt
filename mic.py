
'''
Голосовой ассистент "Крендель 2.0" -> "Ксения" 

from YT channel PythonHubStudio

python 3.8 и выше.

Распаковать в проект языковую модель vosk

Требуется:
pip install vosk
pip install sounddevice
pip install soundfile
pip install scikit-learn
pip install gtts
pip install openai
pip install torch
pip install Pyllow


Ссылки на библиотеки и доп материалы:
sounddevice
https://pypi.org/project/sounddevice/
https://python-sounddevice.readthedocs.io/en/0.4.4/
vosk
https://pypi.org/project/vosk/
https://github.com/alphacep/vosk-api
https://alphacephei.com/vosk/
sklearn
https://pypi.org/project/scikit-learn/
https://scikit-learn.org/stable/
requests
https://pypi.org/project/requests/
gtts
https://gtts.readthedocs.io/en/latest/
openai
https://pypi.org/project/openai/
https://openai.com/

'''

import json
import queue
import os
import sys

from sklearn.feature_extraction.text import CountVectorizer     # pip install scikit-learn
from sklearn.linear_model import LogisticRegression
import sounddevice as sd    #pip install sounddevice
import vosk                 #pip install vosk

import words
import commands               #<<----- так нужно, функции из модуля запускаются через exec(...)
import voices
import chat



q = queue.Queue()

model = vosk.Model('vosk_small')       #голосовую модель vosk нужно поместить в папку с файлами проекта
                                        #https://alphacephei.com/vosk/
                                        #https://alphacephei.com/vosk/models
try:
    device = sd.default.device  # <--- по умолчанию
                                #или -> sd.default.device = 1, 3 или python -m sounddevice просмотр 
    samplerate = int(sd.query_devices(device[0], 'input')['default_samplerate'])  #получаем частоту микрофона
except:
    voices.speaker_silero('Включи микрофон!')
    sys.exit(1)


def callback(indata, frames, time, status):
    '''Очередь с микрофона'''
    q.put(bytes(indata))


def recognize(data, vectorizer, clf):
    '''
    Анализ распознанной речи
    '''
    #Пропускаем все, если длина расспознанного текста меньше 7ми символов
    if len(data) < 7:
        return
    #если нет фразы обращения к ассистенту, то отправляем запрос gpt
    trg = words.TRIGGERS.intersection(data.split())
    if not trg:
        if not int(os.getenv("CHATGPT")):
            return
        voices.speaker_gtts(chat.start_dialogue(data))
        return
    #если была фраза обращения к ассистенту
    #удаляем из команды имя асистента
    data = data.split()
    filtered_data = [word for word in data if word not in words.TRIGGERS]
    data = ' '.join(filtered_data)

    #получаем вектор полученного текста
    #сравниваем с вариантами, получая наиболее подходящий ответ
    # Преобразование команды пользователя в числовой вектор
    user_command_vector = vectorizer.transform([data])

    # Предсказание вероятностей принадлежности к каждому классу
    predicted_probabilities = clf.predict_proba(user_command_vector)

    # Задание порога совпадения
    threshold = 0.2

    # Поиск наибольшей вероятности и выбор ответа, если он превышает порог
    max_probability = max(predicted_probabilities[0])
    print(max_probability)
    if max_probability >= threshold:
        answer = clf.classes_[predicted_probabilities[0].argmax()]
    else:
        voices.speaker_silero("Команда не распознана")
        return
    

    #получение имени функции из ответа из data_set
    func_name = answer.split()[0]

    #озвучка ответа из модели data_set
    voices.speaker_silero(answer.replace(func_name, ''))

    #запуск функции из skills
    exec('commands.' + func_name + '()')


def recognize_wheel():
    print('Слушаем')
    '''
    Обучаем матрицу ИИ для распознавания команд ассистентом
    и постоянно слушаем микрофон
    '''

    # Обучение матрицы на data_set модели
    vectorizer = CountVectorizer()
    vectors = vectorizer.fit_transform(list(words.data_set.keys()))

    clf = LogisticRegression()
    clf.fit(vectors, list(words.data_set.values()))


    # постоянная прослушка микрофона
    with sd.RawInputStream(samplerate=samplerate, blocksize = 16000, device=device[0], dtype='int16',
                            channels=1, callback=callback):

        rec = vosk.KaldiRecognizer(model, samplerate)
        while True and int(os.getenv('MIC')):
            data = q.get()
            if rec.AcceptWaveform(data):
                data = json.loads(rec.Result())['text']
                recognize(data, vectorizer, clf)

    print('Микрофон отключен')

