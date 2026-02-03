# Поиск туров (Tourvisor via eto.travel)

## Шаг 1. Init search
GET https://tourvisor.ru/xml/modsearch.php

Параметры:
- s_country
- s_flyfrom
- s_adults
- s_j_date_from
- s_j_date_to
- s_nights_from
- s_nights_to

Response:
- result.requestid

## Шаг 2. Get results
GET https://search*.tourvisor.ru/modresult.php?requestid=XXXX

Response:
- data.block[].hotel[].tour[]

👉 Всё. Это твой «договор с реальностью».
