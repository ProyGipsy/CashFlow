import re
import numpy as np
import pandas as pd

companies = [
    {
        'name': 'Comercializadora Beauty & Health 18 C.A ',
        'rifType': 'J',
        'rifNumber': '506508435'
    },
    {
        'name': 'Belleza Import 2022. C.A ',
        'rifType': 'J',
        'rifNumber': '500785135'
    },
    {
        'name': 'Chic Import  2021, C.A.',
        'rifType': 'J',
        'rifNumber': '500746113'
    },
    {
        'name': 'Comercializadora Gipsy  CCS, C.A ',
        'rifType': 'J',
        'rifNumber': '506548682'
    },
    {
        'name': 'Comercializadora Remnbd, C.A',
        'rifType': 'J',
        'rifNumber': '504241679'
    },
    {
        'name': 'Corp. 362616, C.A',
        'rifType': 'J',
        'rifNumber': '400189624'
    },
    {
        'name': 'Corporación Braja 36, C.A ',
        'rifType': 'J',
        'rifNumber': '400189519'
    },
    {
        'name': 'Corporación Travelocity C.A ',
        'rifType': 'J',
        'rifNumber': '315059150'
    },
    {
        'name': 'Distribuidora Only & Express C.A ',
        'rifType': 'J',
        'rifNumber': '502715495'
    },
    {
        'name': 'Estetic Import 2020, C.A  ',
        'rifType': 'J',
        'rifNumber': '500735545'
    },
    {
        'name': 'Gipsy de Margarita, C.A ',
        'rifType': 'J',
        'rifNumber': '307424133'
    },
    {
        'name': 'Corporación Ultraya C,A',
        'rifType': 'J',
        'rifNumber': '506253488'
    },
    {
        'name': 'Glow Cosmetics Universal, C.A',
        'rifType': 'J',
        'rifNumber': '506551977'
    },
    {
        'name': 'Importaciones Delicateses 2022, C.A',
        'rifType': 'J',
        'rifNumber': '502719245'
    },
    {
        'name': 'Importadora Pancho 2030, C.A',
        'rifType': 'J',
        'rifNumber': '502716181'
    },
    {
        'name': 'Lácteos Caprinos, C.A.',
        'rifType': 'J',
        'rifNumber': '401958222'
    },
    {
        'name': 'Importaciones Prism Cosmetics, C.A',
        'rifType': 'J',
        'rifNumber': '506865254'
    },
]

rif_list = [
    {
        'docTypeId': 2,
        'companyId': 4,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '506508435'
            },
            {
                'fieldId': 24,
                'value': 'Comercializadora Beauty & Health 18 C.A '
            },
            {
                'fieldId': 25,
                'value': '2025-01-20'
            },
            {
                'fieldId': 26,
                'value': '2025-01-20'
            },
            {
                'fieldId': 110,
                'value': '2028-01-20'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Francisco de Miranda Centro Lido Torre A, Piso 9, Oficina 93-A, Municipio Chacao Estado Miranda'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 5,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '500785135'
            },
            {
                'fieldId': 24,
                'value': 'Belleza Import 2022. C.A '
            },
            {
                'fieldId': 25,
                'value': '2025-02-03'
            },
            {
                'fieldId': 26,
                'value': '2025-03-07'
            },
            {
                'fieldId': 110,
                'value': '2028-03-07'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Francisco de Miranda Centro Lido Torre A, Piso 8, Of 83-A, Urb El Rosal Caracas Municipio Chacao Edo. Miranda'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 6,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '500746113'
            },
            {
                'fieldId': 24,
                'value': 'Chic Import  2021, C.A.'
            },
            {
                'fieldId': 25,
                'value': '2021-01-22'
            },
            {
                'fieldId': 26,
                'value': '2024-01-24'
            },
            {
                'fieldId': 110,
                'value': '2027-01-24'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Libertador CC Centro Comercial Sambil Nivel Acuario Local AC-R30 YRB Chacao Caracas Municipio Chacao Edo. Miranda'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': '2023-03-14'
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 7,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '506548682'
            },
            {
                'fieldId': 24,
                'value': 'Comercializadora Gipsy  CCS, C.A '
            },
            {
                'fieldId': 25,
                'value': '2025-01-29'
            },
            {
                'fieldId': 26,
                'value': '2025-01-29'
            },
            {
                'fieldId': 110,
                'value': '2028-01-29'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Principal de Guayabal, Parcela No. 45 Casa Nro. 45 Urbanización Zona Industrial Guayabal, Guarenas Estado Miranda'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 8,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '504241679'
            },
            {
                'fieldId': 24,
                'value': 'Comercializadora Remnbd, C.A'
            },
            {
                'fieldId': 25,
                'value': '2023-08-18'
            },
            {
                'fieldId': 26,
                'value': '2023-08-18'
            },
            {
                'fieldId': 110,
                'value': '2026-08-18'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Principal de Guayabal Local Nro 45 Urb Guarenas Municipio Plaza, Estado Miranda'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 9,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '400189624'
            },
            {
                'fieldId': 24,
                'value': 'Corp. 362616, C.A'
            },
            {
                'fieldId': 25,
                'value': '2011-12-06'
            },
            {
                'fieldId': 26,
                'value': '2024-05-20'
            },
            {
                'fieldId': 110,
                'value': '2027-05-20'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Jóvito Villalba CC Parque Nivel P/B Local LG3-21 Urbanización Costa Azul Porlamar Municipio Maneiro Estado Nueva Esparta'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 10,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '400189519'
            },
            {
                'fieldId': 24,
                'value': 'Corporación Braja 36, C.A '
            },
            {
                'fieldId': 25,
                'value': '2011-12-06'
            },
            {
                'fieldId': 26,
                'value': '2023-05-08'
            },
            {
                'fieldId': 110,
                'value': '2026-05-08'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Jóvito Villalba CC Parque Costa Azul Nivel P/B Local LH"-05 Urbanizaciónb Costa Azul Porlamar Estado Nueva Esparta'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '304411146'
            },
            {
                'fieldId': 24,
                'value': 'Corporación Gipsy de Venezuela, C. A'
            },
            {
                'fieldId': 25,
                'value': '2000-09-01'
            },
            {
                'fieldId': 26,
                'value': '2025-02-19'
            },
            {
                'fieldId': 110,
                'value': '2028-02-19'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Principal de Guayabal Local Galpón Nro. 45 Urbanización  Guayabal Municipio Plaza, Guarenas Edo. Miranda'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': '2008-07-16'
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 2,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '315055910'
            },
            {
                'fieldId': 24,
                'value': 'Corporación Travel Corner, C. A'
            },
            {
                'fieldId': 25,
                'value': '2006-01-03'
            },
            {
                'fieldId': 26,
                'value': '2022-09-08'
            },
            {
                'fieldId': 110,
                'value': '2025-09-08'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Calle Zona Industrial Local Galpón Nro 45 Sector Guayabal Municipio Plaza Estado Miranda'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 11,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '315059150'
            },
            {
                'fieldId': 24,
                'value': 'Corporación Travelocity C.A '
            },
            {
                'fieldId': 25,
                'value': '2006-01-03'
            },
            {
                'fieldId': 26,
                'value': '2024-01-29'
            },
            {
                'fieldId': 110,
                'value': '2027-01-29'
            },
            {
                'fieldId': 111,
                'value': 'Calle El Pilar, Los Robles Local Centro de Depósitos El Trebol Nro. A 16 Sector Pozo Grande El Pilar (los Robles) Estao Nueva Esparta'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': '2024-12-01'
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 12,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '502715495'
            },
            {
                'fieldId': 24,
                'value': 'Distribuidora Only & Express C.A '
            },
            {
                'fieldId': 25,
                'value': '2022-09-14'
            },
            {
                'fieldId': 26,
                'value': '2022-09-14'
            },
            {
                'fieldId': 110,
                'value': '2025-09-14'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Sur 19 CC Sambil La Candelaria Nivel Mercantil Local M-32-M-046 Urbanización La Candelaria Caracas'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 13,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '500735545'
            },
            {
                'fieldId': 24,
                'value': 'Estetic Import 2020, C.A  '
            },
            {
                'fieldId': 25,
                'value': '2021-01-18'
            },
            {
                'fieldId': 26,
                'value': '2024-01-25'
            },
            {
                'fieldId': 110,
                'value': '2027-01-25'
            },
            {
                'fieldId': 111,
                'value': 'Calle Final Calle Imboca CC Boleíta Center Nivel Plaza Local N1-27 Zona Boleita Municipio Sucre Caracas Petare'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': '2022-10-05'
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 14,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '307424133'
            },
            {
                'fieldId': 24,
                'value': 'Gipsy de Margarita, C.A '
            },
            {
                'fieldId': 25,
                'value': '2001-05-15'
            },
            {
                'fieldId': 26,
                'value': '2024-03-05'
            },
            {
                'fieldId': 110,
                'value': '2027-03-05'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Jovito Villalba CC Costa Azul Nivel P.B Local LG-21 Urbanización Pampatar Estado Nueva Esparta'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 15,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '506253488'
            },
            {
                'fieldId': 24,
                'value': 'Corporación Ultraya C,A'
            },
            {
                'fieldId': 25,
                'value': '2024-11-05'
            },
            {
                'fieldId': 26,
                'value': '2024-11-05'
            },
            {
                'fieldId': 110,
                'value': '2027-11-05'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Orinoco con calle Jalisco Local Coromoto Nro P.B local P.B Urbanizazión Las Mercedes Municipio  Sucre Caracas'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 3,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '307089377'
            },
            {
                'fieldId': 24,
                'value': 'Gipsy Stores, C. A'
            },
            {
                'fieldId': 25,
                'value': '2000-06-01'
            },
            {
                'fieldId': 26,
                'value': '2022-07-11'
            },
            {
                'fieldId': 110,
                'value': '2025-07-11'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Principal CC boleita Center Nivel N1-27 Local 27 Urbanización Boleita Municipio Sucre Caracas'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 16,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '506551977'
            },
            {
                'fieldId': 24,
                'value': 'Glow Cosmetics Universal, C.A'
            },
            {
                'fieldId': 25,
                'value': '2025-01-30'
            },
            {
                'fieldId': 26,
                'value': '2025-01-30'
            },
            {
                'fieldId': 110,
                'value': '2028-01-30'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Francisco de Miranda CC Lido Torre A Nivel 9 Oficina 93A, sector El Rosal Municipio Chacao Caracas'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 17,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '502719245'
            },
            {
                'fieldId': 24,
                'value': 'Importaciones Delicateses 2022, C.A'
            },
            {
                'fieldId': 25,
                'value': '2022-09-15'
            },
            {
                'fieldId': 26,
                'value': '2025-03-07'
            },
            {
                'fieldId': 110,
                'value': '2028-03-07'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Francisco de Miranda Edificio Centro Lido Torre A piso 8 Oficina 83-A Urbanización El Rosal Municipio Chacao Caracas'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': '2025-03-21'
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 18,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '502716181'
            },
            {
                'fieldId': 24,
                'value': 'Importadora Pancho 2030, C.A'
            },
            {
                'fieldId': 25,
                'value': '2023-11-14'
            },
            {
                'fieldId': 26,
                'value': '2023-11-03'
            },
            {
                'fieldId': 110,
                'value': '2026-11-03'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Casanova con calle El Recreo, Nivel C-1 Local L C1-C36 Zona Sabana Grande Municipio Libertador Caracas'
            },
            {
                'fieldId': 162,
                'value': True
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 19,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '401958222'
            },
            {
                'fieldId': 24,
                'value': 'Lácteos Caprinos, C.A.'
            },
            {
                'fieldId': 25,
                'value': '2013-01-29'
            },
            {
                'fieldId': 26,
                'value': '2022-05-18'
            },
            {
                'fieldId': 110,
                'value': '2025-05-18'
            },
            {
                'fieldId': 111,
                'value': 'Avenida Antonio J. Isturiz, entre Avenida Mohedano y Pedregal Qta. Virgen del Valle Urbanización La Castellana Municipio Chacao Estado Miranda'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 2,
        'companyId': 20,
        'fields': [
            {
                'fieldId': 22,
                'value': 'J'
            },
            {
                'fieldId': 23,
                'value': '506865254'
            },
            {
                'fieldId': 24,
                'value': 'Importaciones Prism Cosmetics, C.A'
            },
            {
                'fieldId': 25,
                'value': '2025-04-10'
            },
            {
                'fieldId': 26,
                'value': '2025-04-10'
            },
            {
                'fieldId': 110,
                'value': '2028-04-10'
            },
            {
                'fieldId': 111,
                'value': 'Av Francisco de Miranda Edif Centro Lido, Torre A piso 9 Ofi 93 Sector Chacao Caracas Municipio Chacao Estado Miranda'
            },
            {
                'fieldId': 162,
                'value': False
            },
            {
                'fieldId': 163,
                'value': None
            },
        ]
    },
]

vehicules_list = [
    {
       'docTypeId': 3,
       'companyId': 1,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Corporación Gipsy de Venezuela, C. A'
            },
            {
                'fieldId': 28,
                'value': '28419791'
            },
            {
                'fieldId': 29,
                'value': 'J'
            },
            {
                'fieldId': 30,
                'value': '304411146'
            },
            {
                'fieldId': 31,
                'value': 'A52AB9J'
            },
            {
                'fieldId': 32,
                'value': '8ZCBNJ1718V402617'
            },
            {
                'fieldId': 33,
                'value': '8ZCBNJ1718V402617'
            },
            {
                'fieldId': 34,
                'value': '8ZCBNJ1718V402617'
            },
            {
                'fieldId': 35,
                'value': '18V402617'
            },
            {
                'fieldId': 36,
                'value': 'Chevrolet'
            },
            {
                'fieldId': 37,
                'value': 'NKR/NKRT/MS/AF/H'
            },
            {
                'fieldId': 38,
                'value': 2008
            },
            {
                'fieldId': 39,
                'value': 'Blanco'
            },
            {
                'fieldId': 40,
                'value': 'Camión'
            },
            {
                'fieldId': 41,
                'value': 'Furgon'
            },
            {
                'fieldId': 42,
                'value': 'Carga'
            },
            {
                'fieldId': 43,
                'value': 3
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 1670
            },
            {
                'fieldId': 46,
                'value': 3530
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2009-07-31'
            },
            {
                'fieldId': 49,
                'value': '9311ZG098014'
            },
            {
                'fieldId': 50,
                'value': None
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 1,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Corporación Gipsy de Venezuela, C. A'
            },
            {
                'fieldId': 28,
                'value': '28419792'
            },
            {
                'fieldId': 29,
                'value': 'J'
            },
            {
                'fieldId': 30,
                'value': '304411146'
            },
            {
                'fieldId': 31,
                'value': 'A75AB3J'
            },
            {
                'fieldId': 32,
                'value': '8ZCBNJ1708V402639'
            },
            {
                'fieldId': 33,
                'value': '8ZCBNJ1708V402639'
            },
            {
                'fieldId': 34,
                'value': '8ZCBNJ1708V402639'
            },
            {
                'fieldId': 35,
                'value': '08V402639'
            },
            {
                'fieldId': 36,
                'value': 'Chevrolet'
            },
            {
                'fieldId': 37,
                'value': 'NKR/NKRT/MS/AF/H'
            },
            {
                'fieldId': 38,
                'value': 2008
            },
            {
                'fieldId': 39,
                'value': 'Blanco'
            },
            {
                'fieldId': 40,
                'value': 'Camión'
            },
            {
                'fieldId': 41,
                'value': 'Furgon'
            },
            {
                'fieldId': 42,
                'value': 'Carga'
            },
            {
                'fieldId': 43,
                'value': 3
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 5200
            },
            {
                'fieldId': 46,
                'value': 3530
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2009-07-31'
            },
            {
                'fieldId': 49,
                'value': '9311ZG098218'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 2,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Corporación Travel Corner, C. A'
            },
            {
                'fieldId': 28,
                'value': '30722332'
            },
            {
                'fieldId': 29,
                'value': 'J'
            },
            {
                'fieldId': 30,
                'value': '315055910'
            },
            {
                'fieldId': 31,
                'value': 'A85CD4A'
            },
            {
                'fieldId': 32,
                'value': '8YTSF2A64B8A44641'
            },
            {
                'fieldId': 33,
                'value': '8YTSF2A64B8A44641'
            },
            {
                'fieldId': 34,
                'value': 'BA44641'
            },
            {
                'fieldId': 35,
                'value': 'BA44641'
            },
            {
                'fieldId': 36,
                'value': 'Ford'
            },
            {
                'fieldId': 37,
                'value': '2011'
            },
            {
                'fieldId': 38,
                'value': 2011
            },
            {
                'fieldId': 39,
                'value': 'Blanco'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Pick-Up/C Furgon'
            },
            {
                'fieldId': 42,
                'value': 'Carga'
            },
            {
                'fieldId': 43,
                'value': 3
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 4268
            },
            {
                'fieldId': 46,
                'value': 1639
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2011-12-09'
            },
            {
                'fieldId': 49,
                'value': '205AYD110267'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 2,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Corporación Travel Corner, C. A'
            },
            {
                'fieldId': 28,
                'value': '160102660048'
            },
            {
                'fieldId': 29,
                'value': 'J'
            },
            {
                'fieldId': 30,
                'value': '315055910'
            },
            {
                'fieldId': 31,
                'value': 'A70CR1A'
            },
            {
                'fieldId': 32,
                'value': '8YTSF2A69CGA2301'
            },
            {
                'fieldId': 33,
                'value': None
            },
            {
                'fieldId': 34,
                'value': None
            },
            {
                'fieldId': 35,
                'value': 'CA23601'
            },
            {
                'fieldId': 36,
                'value': 'Ford'
            },
            {
                'fieldId': 37,
                'value': '2012'
            },
            {
                'fieldId': 38,
                'value': 2012
            },
            {
                'fieldId': 39,
                'value': 'Verde'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Furgon'
            },
            {
                'fieldId': 42,
                'value': 'Carga'
            },
            {
                'fieldId': 43,
                'value': 3
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 2629
            },
            {
                'fieldId': 46,
                'value': 1639
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2016-04-07'
            },
            {
                'fieldId': 49,
                'value': '005AYD166067'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 21,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Importadora Leober 18, C.A.'
            },
            {
                'fieldId': 28,
                'value': '140100879865'
            },
            {
                'fieldId': 29,
                'value': 'J'
            },
            {
                'fieldId': 30,
                'value': '400063809'
            },
            {
                'fieldId': 31,
                'value': 'A24BZ6V'
            },
            {
                'fieldId': 32,
                'value': '8YTSF2A64DGA08733'
            },
            {
                'fieldId': 33,
                'value': None
            },
            {
                'fieldId': 34,
                'value': None
            },
            {
                'fieldId': 35,
                'value': 'DA08733'
            },
            {
                'fieldId': 36,
                'value': 'Ford'
            },
            {
                'fieldId': 37,
                'value': '2013'
            },
            {
                'fieldId': 38,
                'value': 2013
            },
            {
                'fieldId': 39,
                'value': 'Negro'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Pick-Up'
            },
            {
                'fieldId': 42,
                'value': 'Carga'
            },
            {
                'fieldId': 43,
                'value': 3
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 2689
            },
            {
                'fieldId': 46,
                'value': 1847
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2014-12-15'
            },
            {
                'fieldId': 49,
                'value': '016AYD044860'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 1,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Corporación Gipsy de Venezuela, C. A'
            },
            {
                'fieldId': 28,
                'value': '140100647844'
            },
            {
                'fieldId': 29,
                'value': 'J'
            },
            {
                'fieldId': 30,
                'value': '304411146'
            },
            {
                'fieldId': 31,
                'value': 'AD410KD'
            },
            {
                'fieldId': 32,
                'value': 'JTEBU17R678081360'
            },
            {
                'fieldId': 33,
                'value': 'JTEBU17R678081360'
            },
            {
                'fieldId': 34,
                'value': 'JTEBU17R678081360'
            },
            {
                'fieldId': 35,
                'value': 'JGR5343142'
            },
            {
                'fieldId': 36,
                'value': 'Toyota'
            },
            {
                'fieldId': 37,
                'value': '4RUNNER LTD V6'
            },
            {
                'fieldId': 38,
                'value': 2007
            },
            {
                'fieldId': 39,
                'value': 'Gris'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Sport Wagon'
            },
            {
                'fieldId': 42,
                'value': 'Particular'
            },
            {
                'fieldId': 43,
                'value': 5
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 1915
            },
            {
                'fieldId': 46,
                'value': 450
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2014-10-15'
            },
            {
                'fieldId': 49,
                'value': '0117TY0447X2'
            },
            {
                'fieldId': 50,
                'value': None
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 1,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Corporación Gipsy de Venezuela, C. A'
            },
            {
                'fieldId': 28,
                'value': '220108034572'
            },
            {
                'fieldId': 29,
                'value': 'J'
            },
            {
                'fieldId': 30,
                'value': '304411146'
            },
            {
                'fieldId': 31,
                'value': 'AA953KM'
            },
            {
                'fieldId': 32,
                'value': 'JTMHT05J885004372'
            },
            {
                'fieldId': 33,
                'value': 'JTMHT05J885004372'
            },
            {
                'fieldId': 34,
                'value': 'JTMHT05J885004372'
            },
            {
                'fieldId': 35,
                'value': '2UZ1265882'
            },
            {
                'fieldId': 36,
                'value': 'Toyota'
            },
            {
                'fieldId': 37,
                'value': 'Land Cruiser Ro/UZJ200L-GNAEK-A'
            },
            {
                'fieldId': 38,
                'value': 2008
            },
            {
                'fieldId': 39,
                'value': 'Negro'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Sport Wagon'
            },
            {
                'fieldId': 42,
                'value': 'Particular'
            },
            {
                'fieldId': 43,
                'value': 8
            },
            {
                'fieldId': 44,
                'value': 3
            },
            {
                'fieldId': 45,
                'value': 2615
            },
            {
                'fieldId': 46,
                'value': 685
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2022-12-30'
            },
            {
                'fieldId': 49,
                'value': '0315TY022243'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 22,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Miguel Neptali Winkler Berman'
            },
            {
                'fieldId': 28,
                'value': '230108279600'
            },
            {
                'fieldId': 29,
                'value': 'V'
            },
            {
                'fieldId': 30,
                'value': '6817974'
            },
            {
                'fieldId': 31,
                'value': 'AC697VB'
            },
            {
                'fieldId': 32,
                'value': 'JTEBU17TR668073225'
            },
            {
                'fieldId': 33,
                'value': 'JTEBU17TR668073225'
            },
            {
                'fieldId': 34,
                'value': 'JTEBU17TR668073225'
            },
            {
                'fieldId': 35,
                'value': '1GR5275677'
            },
            {
                'fieldId': 36,
                'value': 'Toyota'
            },
            {
                'fieldId': 37,
                'value': None
            },
            {
                'fieldId': 38,
                'value': 2006
            },
            {
                'fieldId': 39,
                'value': 'Negro'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Sport Wagon'
            },
            {
                'fieldId': 42,
                'value': 'Particular'
            },
            {
                'fieldId': 43,
                'value': 5
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 1500
            },
            {
                'fieldId': 46,
                'value': 450
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2023-01-13'
            },
            {
                'fieldId': 49,
                'value': '0177TY6331X1'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 22,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Miguel Neptali Winkler Berman'
            },
            {
                'fieldId': 28,
                'value': '210107113657'
            },
            {
                'fieldId': 29,
                'value': 'V'
            },
            {
                'fieldId': 30,
                'value': '6817974'
            },
            {
                'fieldId': 31,
                'value': 'AEJ57R'
            },
            {
                'fieldId': 32,
                'value': 'JTB11VNJ020247365'
            },
            {
                'fieldId': 33,
                'value': 'JTB11VNJ020247365'
            },
            {
                'fieldId': 34,
                'value': 'JTB11VNJ020247365'
            },
            {
                'fieldId': 35,
                'value': '5VZ1502162'
            },
            {
                'fieldId': 36,
                'value': 'Toyota'
            },
            {
                'fieldId': 37,
                'value': None
            },
            {
                'fieldId': 38,
                'value': 2002
            },
            {
                'fieldId': 39,
                'value': 'Beige'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Sport Wagon'
            },
            {
                'fieldId': 42,
                'value': 'Particular'
            },
            {
                'fieldId': 43,
                'value': 5
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 2200
            },
            {
                'fieldId': 46,
                'value': 1900
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2021-11-24'
            },
            {
                'fieldId': 49,
                'value': '027NTY611151'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 22,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Miguel Neptali Winkler Berman'
            },
            {
                'fieldId': 28,
                'value': '230108323440'
            },
            {
                'fieldId': 29,
                'value': 'V'
            },
            {
                'fieldId': 30,
                'value': '6817974'
            },
            {
                'fieldId': 31,
                'value': 'AG297AV'
            },
            {
                'fieldId': 32,
                'value': 'SALLDHM589A651815'
            },
            {
                'fieldId': 33,
                'value': 'SALLDHM589A651815'
            },
            {
                'fieldId': 34,
                'value': None
            },
            {
                'fieldId': 35,
                'value': '15P47142A'
            },
            {
                'fieldId': 36,
                'value': 'Land Rover'
            },
            {
                'fieldId': 37,
                'value': None
            },
            {
                'fieldId': 38,
                'value': 2003
            },
            {
                'fieldId': 39,
                'value': 'Plata'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Sport Wagon'
            },
            {
                'fieldId': 42,
                'value': 'Particular'
            },
            {
                'fieldId': 43,
                'value': 5
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 1600
            },
            {
                'fieldId': 46,
                'value': 400
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2023-02-01'
            },
            {
                'fieldId': 49,
                'value': '007MAR633507'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId':23,
       'fields': [
            {
                'fieldId': 27,
                'value': 'E-MOTORS, C.A. Transporte'
            },
            {
                'fieldId': 28,
                'value': '240109072665'
            },
            {
                'fieldId': 29,
                'value': 'J'
            },
            {
                'fieldId': 30,
                'value': '500727372'
            },
            {
                'fieldId': 31,
                'value': 'A76EU6P'
            },
            {
                'fieldId': 32,
                'value': 'LSKG5GC14SA040084'
            },
            {
                'fieldId': 33,
                'value': None
            },
            {
                'fieldId': 34,
                'value': None
            },
            {
                'fieldId': 35,
                'value': 'R923C006442'
            },
            {
                'fieldId': 36,
                'value': 'Maxus'
            },
            {
                'fieldId': 37,
                'value': 'V80'
            },
            {
                'fieldId': 38,
                'value': 2024
            },
            {
                'fieldId': 39,
                'value': 'Negro'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Panel'
            },
            {
                'fieldId': 42,
                'value': 'Carga'
            },
            {
                'fieldId': 43,
                'value': 16
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 2310
            },
            {
                'fieldId': 46,
                'value': 1190
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2024-05-28'
            },
            {
                'fieldId': 49,
                'value': '022XAZ044657'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 22,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Miguel Neptali Winkler Berman'
            },
            {
                'fieldId': 28,
                'value': '240109037615'
            },
            {
                'fieldId': 29,
                'value': 'V'
            },
            {
                'fieldId': 30,
                'value': '6817974'
            },
            {
                'fieldId': 31,
                'value': 'AD526IA'
            },
            {
                'fieldId': 32,
                'value': 'JTMHT05J084001651'
            },
            {
                'fieldId': 33,
                'value': 'JTMHT05J084001652'
            },
            {
                'fieldId': 34,
                'value': 'JTMHT05J084001653'
            },
            {
                'fieldId': 35,
                'value': '2UZ1244451'
            },
            {
                'fieldId': 36,
                'value': 'Toyota'
            },
            {
                'fieldId': 37,
                'value': 'Land Cruiser Ro'
            },
            {
                'fieldId': 38,
                'value': 2008
            },
            {
                'fieldId': 39,
                'value': 'Beige'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Sport Wagon'
            },
            {
                'fieldId': 42,
                'value': 'Particular'
            },
            {
                'fieldId': 43,
                'value': 5
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 1895
            },
            {
                'fieldId': 46,
                'value': 640
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2024-05-09'
            },
            {
                'fieldId': 49,
                'value': '0075TY644940'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
    {
       'docTypeId': 3,
       'companyId': 1,
       'fields': [
            {
                'fieldId': 27,
                'value': 'Corporación Gipsy de Venezuela, C. A'
            },
            {
                'fieldId': 28,
                'value': '210106719219'
            },
            {
                'fieldId': 29,
                'value': 'V'
            },
            {
                'fieldId': 30,
                'value': '15368469'
            },
            {
                'fieldId': 31,
                'value': 'AJ575VM'
            },
            {
                'fieldId': 32,
                'value': 'JTEBU5JR9J5585264'
            },
            {
                'fieldId': 33,
                'value': None
            },
            {
                'fieldId': 34,
                'value': None
            },
            {
                'fieldId': 35,
                'value': '6CIL'
            },
            {
                'fieldId': 36,
                'value': 'Toyota'
            },
            {
                'fieldId': 37,
                'value': '4Runner'
            },
            {
                'fieldId': 38,
                'value': 2018
            },
            {
                'fieldId': 39,
                'value': 'Negro'
            },
            {
                'fieldId': 40,
                'value': 'Camioneta'
            },
            {
                'fieldId': 41,
                'value': 'Sport Wagon'
            },
            {
                'fieldId': 42,
                'value': 'Particular'
            },
            {
                'fieldId': 43,
                'value': 7
            },
            {
                'fieldId': 44,
                'value': 2
            },
            {
                'fieldId': 45,
                'value': 2095
            },
            {
                'fieldId': 46,
                'value': 760
            },
            {
                'fieldId': 47,
                'value': 'Privado'
            },
            {
                'fieldId': 48,
                'value': '2021-05-11'
            },
            {
                'fieldId': 49,
                'value': '018JTY51144Z'
            },
            {
                'fieldId': 50,
                'value': 'cancelado año 2025'
            },
        ]
    },
]

pw_list = [
    {
        'docTypeId': 4,
        'companyId': 24,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2024-10-29'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '25.2024.4.989'
            },
            {
                'fieldId': 167,
                'value': '2500117378'
            },
            {
                'fieldId': 168,
                'value': 'Corporacion Alivari S.A'
            },
            {
                'fieldId': 52,
                'value': 'Yadira Coromoto Villamizar'
            },
            {
                'fieldId': 53,
                'value': '4141308677'
            },
            {
                'fieldId': 54,
                'value': 'yadirav@corporacioninter.com'
            },
            {
                'fieldId': 55,
                'value': 'Aduanera Servigesa C.A'
            },
            {
                'fieldId': 56,
                'value': 'Gerencia Aduana Principal La Guaira'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Franklin Jose Granadillo'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2025-03-25'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '11.2025.1.1413'
            },
            {
                'fieldId': 167,
                'value': '1100147427'
            },
            {
                'fieldId': 168,
                'value': 'Corporación Gipsy de Venezuela, C. A'
            },
            {
                'fieldId': 52,
                'value': 'Miguel Neptali Winkler '
            },
            {
                'fieldId': 53,
                'value': '4143060405'
            },
            {
                'fieldId': 54,
                'value': 'miguel@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Ivan Luciani C.A'
            },
            {
                'fieldId': 56,
                'value': 'Aduana Principal Aérea de Maiquetía'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Franklin Jose Granadillo'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2023-03-07'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '41754'
            },
            {
                'fieldId': 167,
                'value': '070-00339420'
            },
            {
                'fieldId': 168,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 52,
                'value': 'Miguel Neptali Winkler '
            },
            {
                'fieldId': 53,
                'value': '41413060405'
            },
            {
                'fieldId': 54,
                'value': 'miguel@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Ivan Luciani C.A'
            },
            {
                'fieldId': 56,
                'value': 'Aduana Principal de  La Guaira'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'María Fernanda Palacios Vetancourt'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 5,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2024-10-29'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '25.2024.4.989'
            },
            {
                'fieldId': 167,
                'value': '2500117378'
            },
            {
                'fieldId': 168,
                'value': 'Belleza Import 2022. C.A'
            },
            {
                'fieldId': 52,
                'value': 'Nancy Teresita Fernandez de Navarro'
            },
            {
                'fieldId': 53,
                'value': '4265206278'
            },
            {
                'fieldId': 54,
                'value': 'rrhhhfbas@gmail.com'
            },
            {
                'fieldId': 55,
                'value': 'Aduanera HP 2010, C.A'
            },
            {
                'fieldId': 56,
                'value': 'Principal Marítima de la Guaira'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'María Fernanda Palacios Vetancourt'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 5,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2023-11-21'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '07-225'
            },
            {
                'fieldId': 167,
                'value': '070-00317971'
            },
            {
                'fieldId': 168,
                'value': 'Belleza Import 2022. C.A '
            },
            {
                'fieldId': 52,
                'value': 'Nancy Teresita Fernandez de Navarro'
            },
            {
                'fieldId': 53,
                'value': '4265206278'
            },
            {
                'fieldId': 54,
                'value': 'rrhhhfbas@gmail.com'
            },
            {
                'fieldId': 55,
                'value': 'Empleados'
            },
            {
                'fieldId': 56,
                'value': 'Organismos Públicos o Privados'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'María Fernanda Palacios Vetancourt'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 2,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2017-08-17'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '30-393'
            },
            {
                'fieldId': 167,
                'value': '070-00208408'
            },
            {
                'fieldId': 168,
                'value': 'Corporación Travel Corner, C. A'
            },
            {
                'fieldId': 52,
                'value': 'Miguel Neptali Winkler '
            },
            {
                'fieldId': 53,
                'value': '4143060405'
            },
            {
                'fieldId': 54,
                'value': 'miguel@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Empleados'
            },
            {
                'fieldId': 56,
                'value': 'Organismos Públicos'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Beatriz Rojas Moreno'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 6,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2021-11-23'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '05-225'
            },
            {
                'fieldId': 167,
                'value': '070-00317968'
            },
            {
                'fieldId': 168,
                'value': 'Chic Import  2021, C.A.'
            },
            {
                'fieldId': 52,
                'value': 'Fernando Henao Gutierrez'
            },
            {
                'fieldId': 53,
                'value': '4142125437'
            },
            {
                'fieldId': 54,
                'value': 'fhenao@grugpogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Empleados'
            },
            {
                'fieldId': 56,
                'value': 'Organismos Públicos'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'María Fernanda Palacios Vetancourt'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 13,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2021-11-23'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '22125'
            },
            {
                'fieldId': 167,
                'value': '070-00317972'
            },
            {
                'fieldId': 168,
                'value': 'Estetic Import 2020, C.A'
            },
            {
                'fieldId': 52,
                'value': 'Rita Yudith De La Cruz '
            },
            {
                'fieldId': 53,
                'value': '4241431235'
            },
            {
                'fieldId': 54,
                'value': 'rcruz@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Empleados'
            },
            {
                'fieldId': 56,
                'value': 'Organismos Públicos'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'María Fernanda Palacios Vetancourt'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 9,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2017-08-17'
            },
            {
                'fieldId': 165,
                'value': None
            },
            {
                'fieldId': 166,
                'value': '23579'
            },
            {
                'fieldId': 167,
                'value': '070-00208411'
            },
            {
                'fieldId': 168,
                'value': 'Corp. 362616, C.A'
            },
            {
                'fieldId': 52,
                'value': 'Miguel Neptali Winkler'
            },
            {
                'fieldId': 53,
                'value': '4143060405'
            },
            {
                'fieldId': 54,
                'value': 'miguel@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Santiago Gimón Estrada'
            },
            {
                'fieldId': 56,
                'value': 'Organismos Públicos o Privados'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Beatriz Rojas Moreno'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2019-06-20'
            },
            {
                'fieldId': 165,
                'value': '488-0000-0000'
            },
            {
                'fieldId': 166,
                'value': '5115'
            },
            {
                'fieldId': 167,
                'value': '070-00280958'
            },
            {
                'fieldId': 168,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 52,
                'value': 'Miguel Neptali Winkler'
            },
            {
                'fieldId': 53,
                'value': '4143060405'
            },
            {
                'fieldId': 54,
                'value': 'miguel@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Ana Cabrera'
            },
            {
                'fieldId': 56,
                'value': 'Instituto Nacional de Higiene Rafael Rangel y Sencamer'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Beatriz Rojas Moreno'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 25,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2022-05-23'
            },
            {
                'fieldId': 165,
                'value': '540-756'
            },
            {
                'fieldId': 166,
                'value': '11.2022.2.860'
            },
            {
                'fieldId': 167,
                'value': '1100120835'
            },
            {
                'fieldId': 168,
                'value': 'Sinax Corporation, C.A'
            },
            {
                'fieldId': 52,
                'value': 'Yadira Coromoto Villamizar'
            },
            {
                'fieldId': 53,
                'value': '4141305677'
            },
            {
                'fieldId': 54,
                'value': 'yadirav@corporacioninter.com'
            },
            {
                'fieldId': 55,
                'value': 'Ana Cabrera'
            },
            {
                'fieldId': 56,
                'value': 'Instituto Nacional de Higiene Rafael Rangel y Sencamer'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Irma del Rosario Bermudez'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 14,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2017-08-17'
            },
            {
                'fieldId': 165,
                'value': None
            },
            {
                'fieldId': 166,
                'value': '05-225'
            },
            {
                'fieldId': 167,
                'value': '070-00208414'
            },
            {
                'fieldId': 168,
                'value': 'Gipsy de Margarita, C.A '
            },
            {
                'fieldId': 52,
                'value': 'Miguel Neptali Winkler '
            },
            {
                'fieldId': 53,
                'value': '4143060405'
            },
            {
                'fieldId': 54,
                'value': 'miguel@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Santiago Gimón Estrada'
            },
            {
                'fieldId': 56,
                'value': 'Organismos Públicos o Privados'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Beatriz Rojas Moreno'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 14,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2010-06-21'
            },
            {
                'fieldId': 165,
                'value': None
            },
            {
                'fieldId': 166,
                'value': '6796'
            },
            {
                'fieldId': 167,
                'value': '7118'
            },
            {
                'fieldId': 168,
                'value': 'Gipsy de Margarita, C.A '
            },
            {
                'fieldId': 52,
                'value': 'Miguel Neptali Winkler '
            },
            {
                'fieldId': 53,
                'value': '4143060405'
            },
            {
                'fieldId': 54,
                'value': 'miguel@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Aduanera HP 2010, C.A'
            },
            {
                'fieldId': 56,
                'value': 'Aduana Principal Marítima de la Guaira'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Elizabeth Fidalgo Nunes'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 4,
        'companyId': 14,
        'fields': [
            {
                'fieldId': 51,
                'value': 'Especial'
            },
            {
                'fieldId': 164,
                'value': '2012-03-09'
            },
            {
                'fieldId': 165,
                'value': '7000040838'
            },
            {
                'fieldId': 166,
                'value': '3452'
            },
            {
                'fieldId': 167,
                'value': '070-00040838'
            },
            {
                'fieldId': 168,
                'value': 'Gipsy de Margarita, C.A '
            },
            {
                'fieldId': 52,
                'value': 'Miguel Neptali Winkler '
            },
            {
                'fieldId': 53,
                'value': '4143060405'
            },
            {
                'fieldId': 54,
                'value': 'miguel@grupogipsy.com'
            },
            {
                'fieldId': 55,
                'value': 'Empleados'
            },
            {
                'fieldId': 56,
                'value': 'Organismos Públicos o Privados'
            },
            {
                'fieldId': 57,
                'value': None
            },
            {
                'fieldId': 58,
                'value': None
            },
            {
                'fieldId': 59,
                'value': 'Elizabeth Fidalgo Nunes'
            },
            {
                'fieldId': 60,
                'value': None
            },
            {
                'fieldId': 61,
                'value': None
            },
        ]
    },
]

p_sanit_loc_list = [
    {
        'docTypeId': 20,
        'companyId': 6,
        'fields': [
            {
                'fieldId': 62,
                'value': 'Chic Import 2021 C.A',
            },
            {
                'fieldId': 63,
                'value': 'Remington Recreo',
            },
            {
                'fieldId': 64,
                'value': 'Urbanizacion Sabana Grande Avenida Casanova Con Calle El Recreo, Centro Comercial El Recreo, Nivel C4, Local LC4-23, Parroquia El Recreo Municipio Bolivariano Libertador Distrito Capital',
            },
            {
                'fieldId': 65,
                'value': 'Venta Detal Cosmeticos'
            },
            {
                'fieldId': 66,
                'value': '2023-11-24'
            },
            {
                'fieldId': 67,
                'value': '2024-11-24'
            },
            {
                'fieldId': 68,
                'value': '23-559'
            },
            {
                'fieldId': 69,
                'value': '2023-11-24'
            },
        ]
    },
    {
        'docTypeId': 20,
        'companyId': 6,
        'fields': [
            {
                'fieldId': 62,
                'value': 'Chic Import 2021 C.A',
            },
            {
                'fieldId': 63,
                'value': 'Remington Sambil',
            },
            {
                'fieldId': 64,
                'value': 'Avenida Libertador Centro Comercial Sambil, Nivel Acuario Local ACR-30 Chacao Parroquia Chacao Municipio Chacao Caracas',
            },
            {
                'fieldId': 65,
                'value': 'Destinados a Establecimiento de Cosmeticos'
            },
            {
                'fieldId': 66,
                'value': '2024-03-11'
            },
            {
                'fieldId': 67,
                'value': '2026-03-11'
            },
            {
                'fieldId': 68,
                'value': '1553067'
            },
            {
                'fieldId': 69,
                'value': '2024-03-11'
            },
        ]
    },
    {
        'docTypeId': 20,
        'companyId': 12,
        'fields': [
            {
                'fieldId': 62,
                'value': 'Distribuidora Only & Express C.A',
            },
            {
                'fieldId': 63,
                'value': 'Remington La Candelaria',
            },
            {
                'fieldId': 64,
                'value': 'Avenida Sur 19, Centro Comercial Sambil La Candelaria Nivel Mercantil Local M-032-Ma46 Urbanización La Candelaria Caracas Municipio Libertado Distrito Capital',
            },
            {
                'fieldId': 65,
                'value': 'Destinados a Establecimiento de Cosmeticos'
            },
            {
                'fieldId': 66,
                'value': '2023-09-15'
            },
            {
                'fieldId': 67,
                'value': '2025-09-15'
            },
            {
                'fieldId': 68,
                'value': '1435919'
            },
            {
                'fieldId': 69,
                'value': '2023-09-15'
            },
        ]
    },
    {
        'docTypeId': 20,
        'companyId': 13,
        'fields': [
            {
                'fieldId': 62,
                'value': 'Estetic Import 2020, C.A',
            },
            {
                'fieldId': 63,
                'value': 'Remington Boleíta',
            },
            {
                'fieldId': 64,
                'value': 'Boleíta Norte, Centro Comercial Boleíta Center Nivel Plaza Local N1-27 Parroquia Leoncio Martinez, Municipio Sucre Caracas Estado Miranda',
            },
            {
                'fieldId': 65,
                'value': 'Destinados a Establecimiento de Cosmeticos'
            },
            {
                'fieldId': 66,
                'value': '2024-03-11'
            },
            {
                'fieldId': 67,
                'value': '2026-03-11'
            },
            {
                'fieldId': 68,
                'value': '1552501'
            },
            {
                'fieldId': 69,
                'value': '2024-03-11'
            },
        ]
    },
    {
        'docTypeId': 20,
        'companyId': 14,
        'fields': [
            {
                'fieldId': 62,
                'value': 'Gipsy de Margarita, C.A',
            },
            {
                'fieldId': 63,
                'value': 'Remington Center',
            },
            {
                'fieldId': 64,
                'value': 'Centro Comercial Parque Costa Azul, Nivel PB Local LG3-21 Avenida Jóvito Villalba, Municipio Maneiro Estado Nueva Esparta',
            },
            {
                'fieldId': 65,
                'value': 'Destinados a Establecimiento de Cosmeticos'
            },
            {
                'fieldId': 66,
                'value': '2024-03-11'
            },
            {
                'fieldId': 67,
                'value': '2026-03-11'
            },
            {
                'fieldId': 68,
                'value': '1552330'
            },
            {
                'fieldId': 69,
                'value': '2024-03-11'
            },
        ]
    },
    {
        'docTypeId': 20,
        'companyId': 18,
        'fields': [
            {
                'fieldId': 62,
                'value': 'Importadora Pancho 2030, C.A',
            },
            {
                'fieldId': 63,
                'value': 'Bodegon Recreo',
            },
            {
                'fieldId': 64,
                'value': 'Urbanización Sabana Grande, Avenida Casanova con Calle El Recreo, Centro Comercial El Recreo, Nivel C1- Local No. LC1-C36, Parroquia El Recrep Municipio Bolivariano Libertador Distrito Capital',
            },
            {
                'fieldId': 65,
                'value': 'Venta de Cosméticos y Perfumería'
            },
            {
                'fieldId': 66,
                'value': '2023-11-30'
            },
            {
                'fieldId': 67,
                'value': '2024-11-30'
            },
            {
                'fieldId': 68,
                'value': '23-595'
            },
            {
                'fieldId': 69,
                'value': '2023-11-9'
            },
        ]
    },
]

p_seguros_vh = [
    {
        'docTypeId': 26,
        'companyId': 22,
        'fields': [
            {
                'fieldId': 145,
                'value': 'Land Rover Sport Wagon'
            },
            {
                'fieldId': 146,
                'value': 'Land Rover'
            },
            {
                'fieldId': 147,
                'value': 'AG297AV'
            },
            {
                'fieldId': 148,
                'value': 'Miguel Winkler Berman'
            },
            {
                'fieldId': 149,
                'value': 'Miguel Winkler Berman'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-38382'
            },
            {
                'fieldId': 152,
                'value': '2025-02-02'
            },
            {
                'fieldId': 153,
                'value': '2026-02-02'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 22,
        'fields': [
            {
                'fieldId': 145,
                'value': '4Runner'
            },
            {
                'fieldId': 146,
                'value': 'Toyota'
            },
            {
                'fieldId': 147,
                'value': 'AEJ57R'
            },
            {
                'fieldId': 148,
                'value': 'Miguel Winkler Berman'
            },
            {
                'fieldId': 149,
                'value': 'Miguel Winkler Berman'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-12476'
            },
            {
                'fieldId': 152,
                'value': '2023-12-13'
            },
            {
                'fieldId': 153,
                'value': '2025-12-13'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 22,
        'fields': [
            {
                'fieldId': 145,
                'value': '4Rummer LTD V6'
            },
            {
                'fieldId': 146,
                'value': 'Toyota'
            },
            {
                'fieldId': 147,
                'value': 'AC697VB'
            },
            {
                'fieldId': 148,
                'value': 'Miguel Winkler Berman'
            },
            {
                'fieldId': 149,
                'value': 'Miguel Winkler Berman'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-37702'
            },
            {
                'fieldId': 152,
                'value': '2025-01-19'
            },
            {
                'fieldId': 153,
                'value': '2026-01-19'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 22,
        'fields': [
            {
                'fieldId': 145,
                'value': 'Land Rover'
            },
            {
                'fieldId': 146,
                'value': 'Toyota'
            },
            {
                'fieldId': 147,
                'value': 'AD526IA'
            },
            {
                'fieldId': 148,
                'value': 'Miguel Winkler Berman'
            },
            {
                'fieldId': 149,
                'value': 'Miguel Winkler Berman'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-54445'
            },
            {
                'fieldId': 152,
                'value': '2024-05-15'
            },
            {
                'fieldId': 153,
                'value': '2025-05-15'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 145,
                'value': 'Fortuner'
            },
            {
                'fieldId': 146,
                'value': 'Toyota'
            },
            {
                'fieldId': 147,
                'value': 'AF138LA'
            },
            {
                'fieldId': 148,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 149,
                'value': 'Unión Israelita de Caracas'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-12590'
            },
            {
                'fieldId': 152,
                'value': '2024-02-02'
            },
            {
                'fieldId': 153,
                'value': '2025-02-02'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 145,
                'value': 'Land Cruiser S/Wagon'
            },
            {
                'fieldId': 146,
                'value': 'Toyota'
            },
            {
                'fieldId': 147,
                'value': 'AA953KM'
            },
            {
                'fieldId': 148,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 149,
                'value': 'Unión Israelita de Caracas'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-12585'
            },
            {
                'fieldId': 152,
                'value': '2024-12-31'
            },
            {
                'fieldId': 153,
                'value': '2025-12-31'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 145,
                'value': '4Runner'
            },
            {
                'fieldId': 146,
                'value': 'Toyota'
            },
            {
                'fieldId': 147,
                'value': 'AD410KD'
            },
            {
                'fieldId': 148,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 149,
                'value': 'Unión Israelita de Caracas'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-12594'
            },
            {
                'fieldId': 152,
                'value': '2023-12-31'
            },
            {
                'fieldId': 153,
                'value': '2025-12-31'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 2,
        'fields': [
            {
                'fieldId': 145,
                'value': 'F250 Super Duty'
            },
            {
                'fieldId': 146,
                'value': 'Ford'
            },
            {
                'fieldId': 147,
                'value': 'A85CD4A'
            },
            {
                'fieldId': 148,
                'value': 'Corporación Travel Corner, C.a.'
            },
            {
                'fieldId': 149,
                'value': 'Unión Israelita de Caracas'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-12516'
            },
            {
                'fieldId': 152,
                'value': '2023-12-31'
            },
            {
                'fieldId': 153,
                'value': '2025-12-31'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 145,
                'value': 'NKR 2008'
            },
            {
                'fieldId': 146,
                'value': 'Chevrolet'
            },
            {
                'fieldId': 147,
                'value': 'A52AB9J'
            },
            {
                'fieldId': 148,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 149,
                'value': 'Unión Israelita de Caracas'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-12586'
            },
            {
                'fieldId': 152,
                'value': '2023-12-31'
            },
            {
                'fieldId': 153,
                'value': '2025-12-31'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 145,
                'value': 'NKR 2008'
            },
            {
                'fieldId': 146,
                'value': 'Chevrolet'
            },
            {
                'fieldId': 147,
                'value': 'A75AB3J'
            },
            {
                'fieldId': 148,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 149,
                'value': 'Unión Israelita de Caracas'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-12592'
            },
            {
                'fieldId': 152,
                'value': '2023-12-31'
            },
            {
                'fieldId': 153,
                'value': '2025-12-31'
            },
        ],
    },
    {
        'docTypeId': 26,
        'companyId': 2,
        'fields': [
            {
                'fieldId': 145,
                'value': 'F250 Super Duty'
            },
            {
                'fieldId': 146,
                'value': 'Ford'
            },
            {
                'fieldId': 147,
                'value': 'A70CR1A'
            },
            {
                'fieldId': 148,
                'value': 'Corporación Travel Corner, C.a.'
            },
            {
                'fieldId': 149,
                'value': 'Unión Israelita de Caracas'
            },
            {
                'fieldId': 150,
                'value': 'RCV'
            },
            {
                'fieldId': 151,
                'value': '1-32-51605'
            },
            {
                'fieldId': 152,
                'value': '2024-01-22'
            },
            {
                'fieldId': 153,
                'value': '2025-01-22'
            },
        ],
    },
]

p_seguros_emp = [
    {
        'docTypeId': 27,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 154,
                'value': 'Corporación Gipsy de Venezuela C.A'
            },
            {
                'fieldId': 155,
                'value': 'Avenida.Principal de Guayabal, Galpón 45, Zona Industrial de Guayabal Guarenas Estado Miranda'
            },
            {
                'fieldId': 156,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 157,
                'value': 'Responsabilidad Cívil General'
            },
            {
                'fieldId': 158,
                'value': '1-6-556'
            },
            {
                'fieldId': 159,
                'value': '2024-12-31'
            },
            {
                'fieldId': 160,
                'value': '2025-12-31'
            },
            {
                'fieldId': 161,
                'value': 'Avenida.Principal de Guayabal, Galpón 45, Zona Industrial de Guayabal Guarenas Estado Miranda'
            },
        ]
    },
    {
        'docTypeId': 27,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 154,
                'value': 'Corporación Gipsy de Venezuela C.A'
            },
            {
                'fieldId': 155,
                'value': 'Avenida.Principal de Guayabal, Galpón 45, Zona Industrial de Guayabal Guarenas Estado Miranda'
            },
            {
                'fieldId': 156,
                'value': 'Corporación Gipsy de Venezuela C.A'
            },
            {
                'fieldId': 157,
                'value': 'Todo Riesgo'
            },
            {
                'fieldId': 158,
                'value': '1-44-369'
            },
            {
                'fieldId': 159,
                'value': '2024-12-31'
            },
            {
                'fieldId': 160,
                'value': '2025-12-31'
            },
            {
                'fieldId': 161,
                'value': 'Avenida.Principal de Guayabal, Galpón 45, Zona Industrial de Guayabal Guarenas Estado Miranda'
            },
        ]
    },
    {
        'docTypeId': 27,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 154,
                'value': 'Corporación Gipsy de Venezuela C.A'
            },
            {
                'fieldId': 155,
                'value': 'Avenida.Principal de Guayabal, Galpón 45, Zona Industrial de Guayabal Guarenas Estado Miranda'
            },
            {
                'fieldId': 156,
                'value': 'Corporación Gipsy de Venezuela C.A'
            },
            {
                'fieldId': 157,
                'value': 'Fidelidad 3D'
            },
            {
                'fieldId': 158,
                'value': '1-17-47'
            },
            {
                'fieldId': 159,
                'value': '2024-12-31'
            },
            {
                'fieldId': 160,
                'value': '2025-12-31'
            },
            {
                'fieldId': 161,
                'value': 'Avenida.Principal de Guayabal, Galpón 45, Zona Industrial de Guayabal Guarenas Estado Miranda'
            },
        ]
    },
    {
        'docTypeId': 27,
        'companyId': 2,
        'fields': [
            {
                'fieldId': 154,
                'value': 'Corporación Travel Corner, C.A'
            },
            {
                'fieldId': 155,
                'value': 'Avenida.Principal de Guayabal, Galpón 45, Zona Industrial de Guayabal Guarenas Estado Miranda'
            },
            {
                'fieldId': 156,
                'value': 'Corporación Travel Corner, C.A'
            },
            {
                'fieldId': 157,
                'value': 'Todo Riesgo'
            },
            {
                'fieldId': 158,
                'value': '1-44-409'
            },
            {
                'fieldId': 159,
                'value': '2024-12-31'
            },
            {
                'fieldId': 160,
                'value': '2025-12-31'
            },
            {
                'fieldId': 161,
                'value': 'Avenida.Principal de Guayabal, Galpón 45, Zona Industrial de Guayabal Guarenas Estado Miranda'
            },
        ]
    },
]

patent_list = [
    {
        'docTypeId': 22,
        'companyId': 6,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Chic Import 2021, C.A  Sambil'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 500746113
            },
            {
                'fieldId': 115,
                'value': '2021-09-03'
            },
            {
                'fieldId': 116,
                'value': '30008349'
            },
            {
                'fieldId': 117,
                'value': 'Urbanización Esado Leal, Avenida Libertador, Centro comercial Sambil, Nivel Acuario, Local AC-R30, Municipio Chacao'
            },
            {
                'fieldId': 118,
                'value': 'Chacao'
            },
            {
                'fieldId': 119,
                'value': '2021-11-19'
            },
            {
                'fieldId': 120,
                'value': '2027-03-22'
            },
            {
                'fieldId': 121,
                'value': '15-07-01-U01-008-005-002-001-P02-049'
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 6,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Chic Import 2021, C.A  Recreo'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 500746113
            },
            {
                'fieldId': 115,
                'value': '2021-08-03'
            },
            {
                'fieldId': 116,
                'value': 'CSL-2022-019720'
            },
            {
                'fieldId': 117,
                'value': 'Avenida Casanova con calle El Recreo C.C. El Recreo Sector Sabana GrandeMunicipio Libertador Cistrito Capital'
            },
            {
                'fieldId': 118,
                'value': 'Libertador'
            },
            {
                'fieldId': 119,
                'value': '2024-09-05'
            },
            {
                'fieldId': 120,
                'value': '2027-09-05'
            },
            {
                'fieldId': 121,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 6,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Chic Import 2021, C.A LIDO'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 500746113
            },
            {
                'fieldId': 115,
                'value': '2024-10-15'
            },
            {
                'fieldId': 116,
                'value': '30011061'
            },
            {
                'fieldId': 117,
                'value': 'Urbanización El Rosal, Avenida Francisco de Miranda entre Calle El Parque y calle Naiguatá, Centro Comercial Centro Lido, Torre A, piso 9 Oficina 93-A'
            },
            {
                'fieldId': 118,
                'value': 'Chacao'
            },
            {
                'fieldId': 119,
                'value': '2024-12-05'
            },
            {
                'fieldId': 120,
                'value': '2027-12-05'
            },
            {
                'fieldId': 121,
                'value': '150701U01007006001001P06005'
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 7,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Comercializadora Gipsy CCS, C.A'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 506548682
            },
            {
                'fieldId': 115,
                'value': '2025-03-17'
            },
            {
                'fieldId': 116,
                'value': '10-00256'
            },
            {
                'fieldId': 117,
                'value': 'Avenida Principal de Guayabal, Loca No. 45, Zona Industrial Guayabal Guarenas Estado Miranda'
            },
            {
                'fieldId': 118,
                'value': 'Plaza'
            },
            {
                'fieldId': 119,
                'value': '2024-12-05'
            },
            {
                'fieldId': 120,
                'value': '2027-12-05'
            },
            {
                'fieldId': 121,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 5,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Belleza Import 2022. C.A '
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 500785135
            },
            {
                'fieldId': 115,
                'value': '2025-03-18'
            },
            {
                'fieldId': 116,
                'value': '30012291'
            },
            {
                'fieldId': 117,
                'value': 'Urbanización El Rosal, Avenida Francisco de Miranda entre calle El Parque  y calle Naiguatá, Centro Comercial Centro Lido, Torre A piso 8 Oficina 83-A '
            },
            {
                'fieldId': 118,
                'value': 'Chacao'
            },
            {
                'fieldId': 119,
                'value': '2025-03-18'
            },
            {
                'fieldId': 120,
                'value': '2028-03-18'
            },
            {
                'fieldId': 121,
                'value': '150701U01007006001001P05007'
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 13,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Estetic Import 2020, C.A  '
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 500735545
            },
            {
                'fieldId': 115,
                'value': '2021-08-13'
            },
            {
                'fieldId': 116,
                'value': '100006974 LU-030024758'
            },
            {
                'fieldId': 117,
                'value': 'Urbanización Boleíta Outlet Center, nivel Plaza, piso 1 Loc N1-27, Boleita Sucre Estado Miranda'
            },
            {
                'fieldId': 118,
                'value': 'Sucre'
            },
            {
                'fieldId': 119,
                'value': '2021-08-13'
            },
            {
                'fieldId': 120,
                'value': '2026-12-31'
            },
            {
                'fieldId': 121,
                'value': '15-19-05-U01-420-003-008-001-p01-025'
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 12,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Distribuidora Only & Express, C.A'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 502715495
            },
            {
                'fieldId': 115,
                'value': '2021-08-13'
            },
            {
                'fieldId': 116,
                'value': 'CSL-2023-0000037685'
            },
            {
                'fieldId': 117,
                'value': 'Avenida Sur 19 Centro Comercial Sambil, La Candelaria M-032-M046 La Candelaria'
            },
            {
                'fieldId': 118,
                'value': 'Libertador'
            },
            {
                'fieldId': 119,
                'value': '2023-02-07'
            },
            {
                'fieldId': 120,
                'value': '2027-10-25'
            },
            {
                'fieldId': 121,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 14,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Gipsy de Margarita, C.A'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 307424133
            },
            {
                'fieldId': 115,
                'value': '2021-10-10'
            },
            {
                'fieldId': 116,
                'value': '2005-2452'
            },
            {
                'fieldId': 117,
                'value': 'Avenida Jóvito Villalba, Secor Los Robles, C.C El Parque Costazul, Nivel PB, LG3-21'
            },
            {
                'fieldId': 118,
                'value': 'Manuel Plácido Maneiro'
            },
            {
                'fieldId': 119,
                'value': '2024-06-17'
            },
            {
                'fieldId': 120,
                'value': '2027-06-17'
            },
            {
                'fieldId': 121,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 8,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Comercializadora Remnbd, C.A'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 504241679
            },
            {
                'fieldId': 115,
                'value': '2025-03-17'
            },
            {
                'fieldId': 116,
                'value': '10-00255'
            },
            {
                'fieldId': 117,
                'value': 'Avenida Principal de Guayabal, Local No. 45, Zona Industrial Guayabal Guarenas'
            },
            {
                'fieldId': 118,
                'value': 'Ambrosio Plaza'
            },
            {
                'fieldId': 119,
                'value': '2025-03-17'
            },
            {
                'fieldId': 120,
                'value': '2027-12-31'
            },
            {
                'fieldId': 121,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 1,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Corporación Gipsy de Venezuela, C.A'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 304411146
            },
            {
                'fieldId': 115,
                'value': '2009-11-02'
            },
            {
                'fieldId': 116,
                'value': '10.00142'
            },
            {
                'fieldId': 117,
                'value': 'Zona Industrial Guayabal Galpón 45 Guarenas'
            },
            {
                'fieldId': 118,
                'value': 'Ambrosio Plaza'
            },
            {
                'fieldId': 119,
                'value': '2009-11-02'
            },
            {
                'fieldId': 120,
                'value': '2027-12-31'
            },
            {
                'fieldId': 121,
                'value': None
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 2,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Corporación Travel Corner, C.A'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 315055910
            },
            {
                'fieldId': 115,
                'value': '2010-06-02'
            },
            {
                'fieldId': 116,
                'value': None
            },
            {
                'fieldId': 117,
                'value': 'Calle Industrial Guayabal Edif Parcela 45 Guarenas'
            },
            {
                'fieldId': 118,
                'value': 'Ambrosio Plaza'
            },
            {
                'fieldId': 119,
                'value': '2010-06-11'
            },
            {
                'fieldId': 120,
                'value': None
            },
            {
                'fieldId': 121,
                'value': '10-02369'
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 16,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Glow Cosmetics Universal, C.A'
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 506551977
            },
            {
                'fieldId': 115,
                'value': None
            },
            {
                'fieldId': 116,
                'value': 30012268
            },
            {
                'fieldId': 117,
                'value': 'Urbanización El Rosal, Avenida Francisco de Miranda entre calle El Parque y calle Naiguatá, Centro Comercial Lido, Torre "A", pios 9, Oficina 93-A'
            },
            {
                'fieldId': 118,
                'value': 'Municipio Chacao'
            },
            {
                'fieldId': 119,
                'value': '2025-03-07'
            },
            {
                'fieldId': 120,
                'value': '2028-03-07'
            },
            {
                'fieldId': 121,
                'value': '150701U01007006001001P06008'
            },
        ]
    },
    {
        'docTypeId': 22,
        'companyId': 4,
        'fields': [
            {
                'fieldId': 112,
                'value': 'Comercializadora Beauty & Health 18 C.A '
            },
            {
                'fieldId': 113,
                'value': 'J'
            },
            {
                'fieldId': 114,
                'value': 506508435
            },
            {
                'fieldId': 115,
                'value': None
            },
            {
                'fieldId': 116,
                'value': None
            },
            {
                'fieldId': 117,
                'value': None
            },
            {
                'fieldId': 118,
                'value': None
            },
            {
                'fieldId': 119,
                'value': None
            },
            {
                'fieldId': 120,
                'value': None
            },
            {
                'fieldId': 121,
                'value': None
            },
        ]
    },
]

MAPA_EMPRESAS = {
    "Corporación Gipsy de Venezuela, C. A": 1,
    "Corporación Travel Corner, C. A": 2,
    "Gipsy Stores, C. A": 3,
    "Comercializadora Beauty & Health 18 C.A": 4,
    "Belleza Import 2022. C.A": 5,
    "Chic Import 2021, C.A.": 6,
    "Comercializadora Gipsy CCS, C.A": 7,
    "Comercializadora Remnbd, C.A": 8,
    "Corp. 362616, C.A": 9,
    "Corporación Braja 36, C.A": 10,
    "Corporación Travelocity C.A": 11,
    "Distribuidora Only & Express C.A": 12,
    "Estetic Import 2020, C.A": 13,
    "Gipsy de Margarita, C.A": 14,
    "Corporación Ultraya C,A": 15,
    "Glow Cosmetics Universal, C.A": 16,
    "Importaciones Delicateses 2022, C.A": 17,
    "Importadora Pancho 2030, C.A": 18,
    "Lácteos Caprinos, C.A.": 19,
    "Importaciones Prism Cosmetics, C.A": 20,
    "Importadora Leober 18, C.A.": 21,
    "Miguel Neptali Winkler Berman": 22,
    "E-MOTORS, C.A. Transporte": 23,
    "Corporacion Alivari S.A": 24
}

reg_merc_map = {
    "Empresa":                      {"id": 70,  "type": "textarea"},
    "Registro":                     {"id": 71,  "type": "textarea"},
    "Abogado Redacta Documento":    {"id": 72,  "type": "textarea"},
    "Telefono":                     {"id": 73,  "type": "int"},
    "Correo Electrónico":           {"id": 74,  "type": "textarea"},
    "Fecha de Registro":            {"id": 75,  "type": "date"},
    "Vigencia Empresa":             {"id": 76,  "type": "date"},
    "Tomo":                         {"id": 77,  "type": "text"},
    "Número":                       {"id": 78,  "type": "int"},
    "Expediente":                   {"id": 79,  "type": "textarea"},
    "Domicilio":                    {"id": 80,  "type": "textarea"},
    "Duracion  Empresa":            {"id": 81,  "type": "text"},    # Doble espacio en tu excel
    "Cierre Ejercicio Economico":   {"id": 82,  "type": "text"},
    "Capital":                      {"id": 83,  "type": "float"},
    "Accionista 1":                 {"id": 84,  "type": "textarea"},
    "Porcentaje Acciones Accionista 1": {"id": 85, "type": "float"},
    "Cedula Accionista 1":          {"id": 86,  "type": "int"},
    "Accionista 2":                 {"id": 87,  "type": "textarea"},
    "Porcentaje Acciones Accionista 2": {"id": 88, "type": "float"},
    "Cedula Accionista 2":          {"id": 89,  "type": "int"},
    "Duracion Junta Directiva":     {"id": 90,  "type": "text"},
    "Vencimiento Junta Directiva":  {"id": 91,  "type": "date"},
    "Director ":                    {"id": 92,  "type": "textarea"}, # Espacio al final
    "Teléfono Director":            {"id": 93,  "type": "int"},
    "Correo Director":              {"id": 94,  "type": "textarea"},
    "Director 2":                   {"id": 95,  "type": "textarea"},
    "Teléfono Director2":           {"id": 96,  "type": "int"},
    "Correo Director4":             {"id": 97,  "type": "textarea"},
    "Director 5":                   {"id": 98,  "type": "textarea"}, # Saltaste al 5
    "Teléfono Director6":           {"id": 99,  "type": "int"},
    "Correo Director7":             {"id": 100, "type": "textarea"},
    "Apoderado Judicial ":          {"id": 101, "type": "textarea"}, # Espacio al final
    "Telefono Apoderado Judicial":  {"id": 102, "type": "int"},
    "Correo Apoderado Judicial":    {"id": 103, "type": "textarea"},
    "Comisario ":                   {"id": 104, "type": "textarea"}, # Espacio al final
    "Teléfono Comisario ":          {"id": 105, "type": "int"},      # Espacio al final
    "Correo Comisario ":            {"id": 106, "type": "textarea"}, # Espacio al final
    "Comisario 8":                  {"id": 107, "type": "textarea"},
    "Teléfono Comisario 9":         {"id": 108, "type": "int"},
    "Correo Comisario 10":          {"id": 109, "type": "textarea"}
}

reg_sanit_map = {
    'Marca Producto': 129,
    'Modelo': 130,
    'Descripción': 131,
    'Tipo': 132,
    'Certificado de Aprobación de Modelo': 133,
    'Registro Sanitario': 134,
    'Fecha Emisión': 135,
    'Fecha de Vencimiento': 136
}

def generate_payloads_from_df(df, doc_type_id, company_id, mapping):
    payloads = []

    for index, row in df.iterrows():
        doc_payload = {
            "companyId": company_id,
            "docTypeId": doc_type_id,
            "fields": []
        }

        for col_name, field_id in mapping.items():
            raw_value = row.get(col_name)
            final_value = ""

            # 1. Manejo de Nulos (NaN, NaT, None)
            if pd.isna(raw_value):
                final_value = ""
            
            # 2. Manejo de Fechas (Aquí está el truncado)
            elif isinstance(raw_value, pd.Timestamp) or hasattr(raw_value, 'strftime'):
                # .strftime('%Y-%m-%d') extrae SOLO la fecha (2024-05-08)
                # e ignora completamente la hora.
                final_value = raw_value.strftime('%Y-%m-%d')

            # 3. Manejo de Strings que PARECEN fechas con hora (Caso borde)
            # Si Excel lo leyó como texto "2024-05-08 00:00:00" y no como Timestamp
            elif isinstance(raw_value, str) and ("00:00:00" in raw_value or ":" in raw_value):
                # Intentamos detectar si es una de las columnas de fecha por el nombre
                # o simplemente cortamos por el primer espacio si parece formato ISO
                if "Fecha" in col_name or len(raw_value) >= 10: 
                    try:
                        # Cortamos en el espacio: "2024-05-08 00:00:00" -> "2024-05-08"
                        final_value = raw_value.split(' ')[0] 
                    except:
                        final_value = str(raw_value).strip()
                else:
                    final_value = str(raw_value).strip()

            # 4. Resto de datos
            else:
                final_value = str(raw_value).strip()

            doc_payload["fields"].append({
                "fieldId": field_id,
                "value": final_value
            })

        payloads.append(doc_payload)

    return payloads

# --- 3. FUNCIONES DE LIMPIEZA Y NORMALIZACIÓN ---

def normalize_key(text):
    """
    Convierte 'Chic Import  2021, C.A.' en 'chicimport2021,c.a.'
    para comparaciones a prueba de errores de espacios.
    """
    if not isinstance(text, str): return ""
    # Minúsculas y quitar TODOS los espacios
    return text.lower().replace(" ", "").strip()

def clean_value(value, data_type):
    if pd.isna(value) or value == "": return None
    str_val = str(value).strip()

    if data_type == 'int':
        clean_num = re.sub(r'\D', '', str_val)
        return int(clean_num) if clean_num else None
    elif data_type == 'float':
        clean_num = str_val.replace('%', '').replace(',', '.')
        try:
            return float(clean_num)
        except ValueError:
            return None
    elif data_type == 'date':
        if isinstance(value, pd.Timestamp):
            return value.strftime('%Y-%m-%d')
        if len(str_val) >= 10:
             return str_val[:10]
        return str_val
    else:
        return str_val


def generate_payloads_typed(df, doc_type_id, companies_dict, mapping):
    payloads = []
    skipped_rows = []

    # 1. Crear un diccionario normalizado para búsquedas rápidas
    # Clave: nombre_sin_espacios, Valor: ID
    companies_normalized = {normalize_key(k): v for k, v in companies_dict.items()}

    for index, row in df.iterrows():
        # Obtener nombre tal cual viene en Excel
        raw_company_name = str(row.get("Empresa", ""))
        
        # Normalizar el nombre del Excel (quitar espacios, minúsculas)
        search_key = normalize_key(raw_company_name)

        # Buscar en el diccionario normalizado
        found_company_id = companies_normalized.get(search_key)

        if not found_company_id:
            skipped_rows.append(f"Fila {index+2}: Empresa '{raw_company_name}' no coincide con el diccionario.")
            continue

        doc_payload = {
            "companyId": found_company_id,
            "docTypeId": doc_type_id,
            "fields": []
        }

        for col_name, config in mapping.items():
            # Manejo tolerante de columnas (si falta alguna en el excel)
            if col_name not in df.columns:
                # Intento buscar sin espacios al final (ej: "Director " vs "Director")
                col_name_stripped = col_name.strip()
                if col_name_stripped in df.columns:
                    raw_value = row.get(col_name_stripped)
                else:
                    continue # Si no existe, pasamos
            else:
                raw_value = row.get(col_name)

            final_value = clean_value(raw_value, config.get('type', 'text'))
            value_str = str(final_value) if final_value is not None else ""

            doc_payload["fields"].append({
                "fieldId": config['id'],
                "value": value_str
            })

        payloads.append(doc_payload)

    if skipped_rows:
        print("\n⚠️  FILAS OMITIDAS (Revisar nombres en Diccionario):")
        for msg in skipped_rows:
            print(msg)
            
    return payloads