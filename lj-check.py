## coding=UTF-8

# Проверка всехс страниц аккаунта ЖЖ
# на наличие недопустимых ссылок
# Версия 0.8
lj_check = '0.8'
# 2023-02-25

# СДЕЛАТЬ: 
# добавить в отчёт ссылку на реестр неджелательных организаций (через файл списка доменов)
# добавить в отчёт версию и дату списка опасных доменов
# архивирование страниц
# включить публикации в группах
# включить комментарии
# зашифровать список опасных доменов ?
# однократное скачивание страниц (было до версии 0.8)
# СДЕЛАНО
# закачивание всего через RPC
# Добавить прогресс выполенния

import bs4, datetime, hashlib, os, re, requests, sys, webbrowser, xmlrpc.client

# Рабочий каталог программы
path_work = os.getcwd()

# разделитель для разных ОС
if os.name in ('nt'):
    SEPARATOR = '\\'
else:
    SEPARATOR = '/'

print('===== lj_check ===  версия 0.6 =====\nПрограмма находит все страницы выбранного профиля\nЖивого журнала (livejournal.com) и проверяет все\nссмлки на наличие в адресе доменов организаций,\nприхзнанных в РФ нежелательными.\nСписолк доменов пополняется, поэтмоу проверку лучше\nпрвоодить регулярно.\nИтогом работы программы является отчёт в виде HTNL-файла,\nкоторый появится в каталоге, из которого вы запустили\nданную программу.\nВсе проверенные страницы будут\nсохранены в подкаталоге с именем пользователя.\nПрограмма не удаляет ссылки, за которые могут\nпривлечь к уголовной ответственнсоти - вам надо\nэто сделать вручную со страниц, указанных в отчёте.\n')

# Ввод имени пользователя
user = input('Введите имя пользователся > ')
password = input('Введите пароль > ')
print('\r' + ' ' * (17 + len(password)), end = '\r')

user = user.lower()
user_domain = user.replace('_', '-')
url_root = 'https://' + user_domain + '.livejournal.com/'

# Папка для скачанных страниц
path_html = path_work + SEPARATOR + user_domain
#try
if not os.path.exists(path_html):
    os.mkdir(path_html)

# начало работы программы
time_start = datetime.datetime.now()

hpassword = hashlib.md5(password.encode('utf-8')).hexdigest()
password = ''
proxy = xmlrpc.client.ServerProxy('http://www.livejournal.com/interface/xmlrpc')

c = proxy.LJ.XMLRPC.getchallenge()['challenge']
r = hashlib.md5((c+hpassword).encode('utf-8')).hexdigest()

params2 = {'username': user, 
'auth_method': 'challenge',  
'auth_challenge': c,
'auth_response': r,
'ver': 1,
'clientversion': 'python_lj-check/0.7.3 galitsky@mail.ru'
}
try:
    res = proxy.LJ.XMLRPC.login(params2)
except:
    print('Некорректная пара пользователь/пароль')
    print('\nСообщения о проблемах, замечания и предлдожения направлять\nна galitsky@mail.ru или в Телеграм @denis_galitsky')
    input('Нажмите Enter для завершения...')
    sys.exit()     
print('Пользователь и пароль верные.')

url_root = 'https://' + user_domain + '.livejournal.com/'

pattern_user = re.compile('^https?://(.+)\.livejournal\.com/')
# Опасные домены
#try
url_find = bytes.decode(requests.get('http://storojok-perm.ru/url_check/url_check.txt').content).split('\n')
url_find.pop(0)
##########
#url_find.append('garant.ru')

pattern_domain = []
for i in url_find:
    pattern_domain.append(re.compile('[\./]' + i.replace('.', '\.') + '/*'))
#----------------- HTML-отчёт --------------------------------------
html_log = bs4.BeautifulSoup('<h1>Отчёт по поиску опасных ссылок</h1>', 'lxml')
tag_up = html_log.new_tag('div')
html_log.body.append(tag_up)
tag0 = html_log.new_tag('p')
tag_up.append(tag0)
tag0.string = 'Программа lj-check версии ' + lj_check
tag0 = html_log.new_tag('p')
tag_up.append(tag0)
tag0.string = 'Пользователь LiveJournal.com: '
tag1 = html_log.new_tag('b')
tag0.append(tag1)
tag1.string = user
tag0 = html_log.new_tag('p')
tag_up.append(tag0)
tag0.string = 'Домашняя страница: '
tag1 = html_log.new_tag('a', href = url_root) 
tag0.append(tag1)
tag1.string = url_root
tag0 = html_log.new_tag('p')
tag_up.append(tag0)
tag0.string = 'Дата проверки: ' + str(datetime.datetime.now().replace(microsecond=0)) 
tag0 = html_log.new_tag('h2')
html_log.body.append(tag0)
#tag0 = bs4.Comment('Искомые адреса: ' + ' , '.join(url_find))
#tag_up.append(tag0)
tag_list = html_log.new_tag('ol')
html_log.body.append(tag_list)

#----------------- Выкачивание и проверка страниц ------------------
last = '2001-01-01 00:00:00'    
count = 0 # количесвто просмотренных страниц
size = 0 # объём скачавнных страниц
#percent = 0 # процент просмотренных страниц
url_found = 0 # найденные сcылки
pages_found = 0 # найденные страницы
page_count = 0 # общее количество обрабюотанных станиц
progress = 0 # общее количество загруженных станиц
while 1:
    c = proxy.LJ.XMLRPC.getchallenge()['challenge']
    r = hashlib.md5((c+hpassword).encode('utf-8')).hexdigest()
    params3 = {'username': user, 
    'auth_method': 'challenge',  
    'auth_challenge': c,
    'auth_response': r,
    'ver': 1,
    'clientversion': 'lj-check',
    'lastsync': last,
    'selecttype': 'syncitems',
    'howmany': '50',
    'lineendings': 'unix'
    }
    res = proxy.LJ.XMLRPC.getevents(params3)
    if len(res['events']) == 0:
        break
    progress += len(res['events'])
    print (f'Загружено страниц: {progress}\r', end='')
    for i in range(len(res['events'])): 
        page_count += 1
        url = res['events'][i]['url']
        # Выделение имени файла
        n = re.search(r'\d+\.[Hh][Tt][Mm][Ll]$', url)
        if url.startswith(url_root): 
            p = path_html + SEPARATOR + n[0]
        else:  
            u = pattern_user.search(url)[1]
            p = path_html + SEPARATOR + u
            if not os.path.exists(p):
                os.mkdir(p)
            p = p + SEPARATOR + n[0]
        
        if isinstance(res['events'][i]['subject'], str):
            title = res['events'][i]['subject']
        else:
            title =  res['events'][i]['subject'].data.decode("UTF-8")
        if isinstance(res['events'][i]['event'], str):
            htmlpage = res['events'][i]['event']
        else:
            htmlpage =  res['events'][i]['event'].data.decode("UTF-8")
        # Запись файла HTML
        h = '<html><body><a href="' + url +'"><h1>' + title + '</h1></a><p><i>' + res['events'][i]['eventtime'] +'</i></p>' + htmlpage + '</body></html>'
        f = open(p, 'w', encoding='utf-8')
        f.write(h)
        f.close()
        size += len(h)
        if res['events'][i]['eventtime'] > last:
            last = res['events'][i]['eventtime']
        
        soup = bs4.BeautifulSoup(htmlpage, 'lxml')
        # Поиск ссылок на странице
        x = 0
        tag_url = html_log.new_tag('li')
        tag_list.append(tag_url)
        tag1 = html_log.new_tag('a', href = url)
        tag_url.append(tag1)
        tag1b = html_log.new_tag('b')
        tag1.append(tag1b)
        tag1b.string = title
        if not url.startswith(url_root):
            tag1b = html_log.new_tag('span')
            tag_url.append(tag1b)
            tag1b.string = ' - удалиять нужно ваш '
            tag1c = html_log.new_tag('mark')
            tag1b.append(tag1c)
            tag1d = html_log.new_tag('a', href = url)
            tag1c.append(tag1d)
            tag1d.string = 'репост'
        tag2 = html_log.new_tag('ul')
        tag_url.append(tag2)
        for link in soup.find_all('a'):
            a = link.get('href')
            if not ((a is None) or (a == '')):
                for pattern in pattern_domain:
                    if pattern.search(a):
                        # Запись в html-отчёт
                        tag3 = html_log.new_tag('li')
                        tag2.append(tag3)
                        tag4 = html_log.new_tag('a', href = a)
                        tag3.append(tag4)
                        tag4i = html_log.new_tag('i')
                        tag4.append(tag4i)
                        tag4i.string = link.text
                        x += 1
                        break  
        if x > 0:
            url_found += x
            pages_found += 1
        else:
            tag_url.decompose()

#----------------- Итога работы ------------------------------------
if url_found == 0:
    print (f'\nОпасные ссылки не найдены!')
    html_log.h2.string = 'Опасных ссылок не найдено!'
    html_log.h2['style'] = 'color:green'
else:
    print (f'\nНайдено {url_found} опастных ccылок на {pages_found} страницах!!!\nНеобхзодимо произвести удалние вручную.')
    html_log.h2.string = 'На ' + str(pages_found) + ' страницах найдено ' + str(url_found) + ' опасных ccылок. Удалите вручную!'
    html_log.h2['style'] = 'color:red'
tag0 = html_log.new_tag('hr')
html_log.body.append(tag0)
tag0 = html_log.new_tag('p')
html_log.body.append(tag0)
tag0.string = 'Время работы программы: ' + str(datetime.datetime.now() - time_start)
tag0 = html_log.new_tag('p')
html_log.body.append(tag0)
tag0.string = 'Общее количество проверенных и сохранённых на компьютере страниц пользователя: '
tag1 = html_log.new_tag('a', href = 'file://' + path_html)
tag0.append(tag1)
tag1.string = str(page_count)
tag0 = html_log.new_tag('p')
html_log.body.append(tag0)
tag0.string = ('Общий объём сохранённых на компьютере страниц пользователя: ' + format(size/1048576, '0.2f') + ' Мбайт')
tag0 = html_log.new_tag('p')
html_log.body.append(tag0)
tag0.string = 'Сообщения о проблемах, замечания и предлдожения направлятьна '
tag1 = html_log.new_tag('a', href = 'mailto:galitsky@mail.ru')
tag0.append(tag1)
tag1.string = 'galitsky@mail.ru'
tag1 = html_log.new_tag('span')
tag0.append(tag1)
tag1.string = ' или в Телеграм '
tag1 = html_log.new_tag('a', href = 'http://t.me/Denis_Galitsky')
tag0.append(tag1)
tag1.string = '@Denis_Galitsky'

print('\nСообщения о проблемах, замечания и предлдожения направлять\nна galitsky@mail.ru или в Телеграм @denis_galitsky')

html_log_file = open(path_work + SEPARATOR + user +'_report.html', 'w', encoding='utf-8')
html_log_file.write(str(html_log))
html_log_file.close()

input('\nНажмите Entr для завершения - отчёт будет открыт в браузере...')

webbrowser.open_new_tab(path_work + SEPARATOR + user +'_report.html')
