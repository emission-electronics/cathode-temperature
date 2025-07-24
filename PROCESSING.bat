@ECHO off

REM Активируем виртуальное окружение
call .venv\Scripts\activate.bat

REM Создаём алиас proc с помощью doskey
doskey proc=python src\method_processing\main.py $*

REM Выводим сообщение
echo Alias 'proc' created for processing function. Type 'proc --help' for usage.

REM Остаёмся в командной строке
cmd /k
