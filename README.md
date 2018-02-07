
# Test_Work_RTEC


## Запуск:

git clone https://github.com/as-korchagin/Test_Work_RTEC.git
cd ./Test_Work_RTEC

 1. python3 ./notesRest.py
 2. python3 ./testNotesREST.py
 3. python3 ./notesRestDbConnected.py #кодировка атрибутов note и description в БД - utf8_general_ci 
## Зависимости:
Задание 1: все используемые библиотеки идут в комплекте с python3
Задание 2: используется библиотека requests (pip3 install requests)
Задание 3: используется библиотека MySqlDb (pip3 install mysqlclient) и сервер СУДБ MySQL (mysql-server 5.7.21-0ubuntu0.16.04.1)

## Результаты тестирования:

notesRest:

Входные данные:
Number of checks: 1000
Add/Delete: 5/2

Выходные данные:
Mean: 0.008760086258776329 seconds
Operations completed: 997
Errors: 0
Bytes sent: 1383836

notesRestDbConnected:

Входные данные:
Number of checks: 1000
Add/Delete: 5/2

Выходные данные:
Mean: 0.04568528828828829 seconds
Operations completed: 999
Errors: 0
Bytes sent: 1386612

