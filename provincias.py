"""
Provincias y municipios de Cuba - datos completos
"""

PROVINCIAS_MUNICIPIOS = {
    "Pinar del Río": [
        "Consolación del Sur", "Guane", "La Palma", "Los Palacios",
        "Mantua", "Minas de Matahambre", "Pinar del Río",
        "San Luis", "Sandino", "Viñales"
    ],
    "Artemisa": [
        "Alquízar", "Artemisa", "Bahía Honda", "Bauta", "Caimito",
        "Candelaria", "Güira de Melena", "Mariel",
        "San Antonio de los Baños", "San Cristóbal"
    ],
    "La Habana": [
        "Arroyo Naranjo", "Boyeros", "Centro Habana", "Cerro",
        "Cotorro", "Diez de Octubre", "Guanabacoa", "Habana del Este",
        "Habana Vieja", "La Lisa", "Marianao", "Playa",
        "Plaza de la Revolución", "Regla", "San Miguel del Padrón"
    ],
    "Mayabeque": [
        "Batabanó", "Bejucal", "Güines", "Jaruco", "Madruga",
        "Melena del Sur", "Nueva Paz", "Quivicán",
        "San José de las Lajas", "San Nicolás de Bari",
        "Santa Cruz del Norte"
    ],
    "Matanzas": [
        "Calimete", "Cárdenas", "Ciénaga de Zapata", "Colón",
        "Jagüey Grande", "Jovellanos", "Limonar", "Los Arabos",
        "Matanzas", "Pedro Betancourt", "Perico", "Unión de Reyes"
    ],
    "Cienfuegos": [
        "Abreus", "Aguada de Pasajeros", "Cienfuegos", "Cruces",
        "Cumanayagua", "Lajas", "Palmira", "Rodas",
        "Santa Isabel de las Lajas"
    ],
    "Villa Clara": [
        "Caibarién", "Camajuaní", "Cifuentes", "Corralillo",
        "Encrucijada", "Manicaragua", "Placetas",
        "Quemado de Güines", "Ranchuelo", "Remedios",
        "Sagua la Grande", "Santa Clara", "Santo Domingo"
    ],
    "Sancti Spíritus": [
        "Cabaiguán", "Fomento", "Jatibonico", "La Sierpe",
        "Sancti Spíritus", "Trinidad", "Yaguajay"
    ],
    "Ciego de Ávila": [
        "Baraguá", "Bolivia", "Chambas", "Ciego de Ávila",
        "Florencia", "Majagua", "Morón", "Primero de Enero", "Venezuela"
    ],
    "Camagüey": [
        "Camagüey", "Carlos Manuel de Céspedes", "Esmeralda",
        "Florida", "Guáimaro", "Jimaguayú", "Minas", "Najasa",
        "Nuevitas", "Santa Cruz del Sur", "Sibanicú",
        "Sierra de Cubitas", "Vertientes"
    ],
    "Las Tunas": [
        "Amancio", "Colombia", "Jesús Menéndez", "Jobabo",
        "Las Tunas", "Majibacoa", "Manatí", "Puerto Padre"
    ],
    "Holguín": [
        "Antilla", "Báguanos", "Banes", "Cacocum",
        "Calixto García", "Cueto", "Frank País", "Gibara",
        "Holguín", "Mayarí", "Moa", "Rafael Freyre",
        "Sagua de Tánamo", "Urbano Noris"
    ],
    "Granma": [
        "Bartolomé Masó", "Bayamo", "Buey Arriba", "Campechuela",
        "Cauto Cristo", "Guisa", "Jiguaní", "Manzanillo",
        "Media Luna", "Niquero", "Pilón", "Río Cauto", "Yara"
    ],
    "Santiago de Cuba": [
        "Contramaestre", "Guamá", "Mella", "Palma Soriano",
        "San Luis", "Santiago de Cuba", "Segundo Frente",
        "Songo-La Maya", "Tercer Frente"
    ],
    "Guantánamo": [
        "Baracoa", "Caimanera", "El Salvador", "Guantánamo",
        "Imías", "Maisí", "Manuel Tames", "Niceto Pérez",
        "San Antonio del Sur", "Yateras"
    ],
    "Isla de la Juventud": [
        "Nueva Gerona"
    ]
}

LISTA_PROVINCIAS = list(PROVINCIAS_MUNICIPIOS.keys())


def get_municipios(provincia: str) -> list:
    return PROVINCIAS_MUNICIPIOS.get(provincia, [])


def provincia_valida(provincia: str) -> bool:
    return provincia in PROVINCIAS_MUNICIPIOS


def municipio_valido(provincia: str, municipio: str) -> bool:
    return municipio in PROVINCIAS_MUNICIPIOS.get(provincia, [])
