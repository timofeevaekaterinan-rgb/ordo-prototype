# Собирает index.html для GitHub Pages из prototype/index.html.
# Исходник прототипа написан под артефакт (без doctype/head), здесь он оборачивается в полноценную страницу.
import pathlib

root = pathlib.Path(__file__).parent
src = (root / 'prototype' / 'index.html').read_text(encoding='utf-8')
cut = src.index('</style>') + len('</style>')
head, body = src[:cut], src[cut:]
page = f'''<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="robots" content="noindex, nofollow">
{head}
<style>body{{margin:0}}</style>
</head>
<body>
{body}
</body>
</html>
'''
(root / 'index.html').write_text(page, encoding='utf-8')
print('index.html:', len(page), 'байт')
