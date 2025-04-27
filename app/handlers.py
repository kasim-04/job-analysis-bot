import requests
import numpy as np
import os

from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()
router = Router()
url = 'https://api.hh.ru/vacancies'


@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        'Здравствуйте! Отправьте мне название профессии, и я расскажу, сколько Вы можете заработать! 💰\n\n'
        'Если у Вас остались вопросы, нажмите /help'
    )


@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer(
        '<b>Как использовать бота</b>:\n'
        '1. Введите профессию: Напишите название вашей профессии.\n'
        '2. Получите информацию: Бот проанализирует данные и предоставит Вам информацию о диапазоне зарплат.',
        parse_mode='HTML'
    )


@router.message()
async def get_stats(message: Message):
    job = message.text

    if job:
        await message.answer('Пожалуйста, подождите немного! ⏳')

        headers = {'User-Agent': os.getenv('USER_AGENT')}
        params = {
            'text': f'{job}',
            'area': 1,
            'per_page': 100,
        }
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            total_pages = response.json()['pages']

            salaries = []
            for i in range(total_pages):
                params['page'] = i
                response = requests.get(url, params=params, headers=headers)

                if response.status_code == 200:
                    items = response.json()['items']

                    for item in items:
                        salary = item['salary']

                        if salary is not None and salary['currency'] == 'RUR':
                            if salary['from'] is not None and salary['to'] is not None:
                                salaries.append((salary['from'] + salary['to']) / 2)
                            elif salary['from'] is not None:
                                salaries.append(salary['from'])
                            else:
                                salaries.append(salary['to'])

            if len(salaries) >= 30:
                data = np.array(salaries)
                q_1 = round(np.percentile(data, 25))
                q_3 = round(np.percentile(data, 75))
                await message.reply(
                    f'Зарплата составляет:\n'
                    f'<b>{q_1 // 1000} 000 - {q_3 // 1000} 000 ₽</b>\n\n'
                    f'Удачи Вам в поисках и достижении целей!',
                    parse_mode='HTML'
                )

            else:
                await message.reply(
                    'К сожалению, по данному запросу не удалось собрать достаточно данных. 🤔\n\n'
                    'Попробуйте уточнить Ваш запрос. Я всегда готов помочь!'
                )

        else:
            await message.reply(
                f'Извините, по данному запросу получена ошибка {response.status_code}. 🤔\n\n'
                f'Попробуйте уточнить Ваш запрос. Я всегда готов помочь!'
            )

    else:
        await message.answer(
            'Извините, но я обрабатываю только текстовые сообщения.\n\n'
            'Если Вам нужна подробная инструкция, просто нажмите /help.'
        )
