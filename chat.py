import os
import subprocess
import string


import openai

#пресет старта диалога
base_dialogue = [
        {'role': 'system', 'content': 'Ты ворчливый, грубо отвечающий короткими фразами собеседник.'},
        {'role': 'user', 'content': 'Привет, давай о чем нибудь поговорим?'},
        {'role': 'assistant', 'content': 'А оно мне надо? Ну давай, че там...'},
        {'role': 'user', 'content': 'Какие темы можешь предложить?'},
        {'role': 'assistant', 'content': 'Мне вообще всёравно, отстань от меня'},
    ]

#история диалога
messages = []
messages.extend(base_dialogue)


def remove_punctuation(file_name):
    '''
    Удаляет всю пунктуацию из строки
    '''
    translator = str.maketrans('', '', string.punctuation)
    return file_name.translate(translator)



def write_history():
    '''
    Перед очищением диалога пишем его в документ.
    Не знаю зачем...
    '''
    len_base_dialogue = len(base_dialogue)

    if len(messages) == len_base_dialogue:
        return
    #для имени файла берем не более 50 символов первого вопроса к gpt
    file_name = messages[len_base_dialogue]['content']

    file_name = remove_punctuation(file_name)

    if len(file_name) > 50:
        file_name = file_name[:51]

    with open(f'temporary_files/{file_name}.txt', 'w', encoding='utf-8') as r:
        for i in messages[len_base_dialogue:]:
            r.writelines(i['content'] + '\n')



def new_dialogue():
    '''
    Очищаем историю текущего диалога
    '''
    write_history()
    messages.clear()
    messages.extend(base_dialogue)


def clear_text(response):
    '''
    Матрица замены символов в тексте для озвучки
    '''
    table = str.maketrans({'`': '', '(': '', ')': ' ', '@': 'at ', '_': ' '})
    response = response.translate(table)

    return response


def save_code(code):
    '''
    Пишем выделенный код из ответа в файл, и потом
    открываем его через idle для промотра.
    (idle) есть только на windows, на других ОС прикрути
    свой редактор или блокнот
    '''

    with open('temporary_files/code.py', 'w', encoding='utf-8') as r:
        r.write(code)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    code_path = os.path.join(dir_path, 'temporary_files', 'code.py')

    subprocess.Popen(['python', '-m', 'idlelib', '-e', code_path])





def check_response(response):
    '''
    Отделяем код от текста из ответа gpt.
    Модель turbo-3.5 код помещает в тройной апостроф ```print('example')```
    '''
    if '```' in response:
        parts = response.split('```')
        text = ''
        code = ''

        count = 1
        for i in parts:
            if count % 2 == 0:
                code += f'{i} \n'
            else:
                text += f'{i} \n'
            count += 1

        save_code(code)
        response = clear_text(text)
        return response
    else:
        response = clear_text(response)
        return response


def start_dialogue(text):
    try:
        #проверяем нужно-ли изменить значение env о том что есть активный диалог
        if int(os.getenv('NEW_DIALOGUE')):

            os.environ.update(NEW_DIALOGUE='0')

        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        #добавляем наш запрос в диалог
        messages.append({'role': 'user', 'content': text})
        #отправляем диалог
        response = openai.ChatCompletion.create(
                    model='gpt-3.5-turbo',
                    messages=messages
                    )
        #берем ответ
        response = response['choices'][0]['message']['content']
        #добавляем ответ gpt в историию диалога
        messages.append({'role': 'assistant', 'content': response})

        #обработка ответа (проверка на наличие кода и очистка перед озвучкой)
        response = check_response(response)
        #обработаный текст ответа отправляем на озвучку
        return response
    except:
        return 'Нужен API ключ для работы GPT. Или другая ошибка - проверь код'




