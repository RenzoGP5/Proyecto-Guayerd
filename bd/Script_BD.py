import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta
import re
import os
from bd.detalle_ventas_mejorado import generar_tabla_detalle_ventas_mejorada, validar_detalle_ventas


# Configuración
fake = Faker(['es_AR'])  
random.seed(42)  # Para reproducibilidad

# Parámetros del negocio
NUM_CLIENTES = 576
FECHA_INICIO_NEGOCIO = datetime(2023, 1, 1)
FECHA_HOY = datetime(2024, 10, 31)

# Ciudades de Argentina
BARRIOS_BA = [
    'Palermo', 'Recoleta', 'Belgrano', 'Caballito', 'Villa Crespo',
    'Almagro', 'Flores', 'Villa Urquiza', 'Núñez', 'Colegiales'
]

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def limpiar_texto(texto):
    """Remueve tildes y caracteres especiales para emails"""
    texto = texto.lower()
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    for orig, reempl in reemplazos.items():
        texto = texto.replace(orig, reempl)
    return texto

def generar_email(nombre_completo):
    """Genera email correlacionado con el nombre"""
    partes = nombre_completo.split()
    
    if len(partes) >= 2:
        nombre = limpiar_texto(partes[0])
        apellido = limpiar_texto(partes[-1])
    else:
        nombre = limpiar_texto(partes[0])
        apellido = ""
    
    # Diferentes formatos realistas
    formatos = [
        f"{nombre}.{apellido}",
        f"{nombre}{apellido}",
        f"{nombre}_{apellido}",
        f"{nombre}.{apellido}{random.randint(1,99)}",
        f"{nombre[0]}{apellido}",
    ]
    
    formato = random.choice(formatos)
    dominios = ['@gmail.com', '@hotmail.com', '@outlook.com', '@yahoo.com']
    
    return formato + random.choice(dominios)

def generar_fecha_alta():
    """Genera fecha de registro con distribución realista"""
    # 60% clientes antiguos (2023), 40% clientes nuevos (2024)
    if random.random() < 0.6:
        return fake.date_time_between(
            start_date=FECHA_INICIO_NEGOCIO,
            end_date=datetime(2023, 12, 31)
        )
    else:
        return fake.date_time_between(
            start_date=datetime(2024, 1, 1),
            end_date=FECHA_HOY
        )

# ============================================================
# GENERACIÓN DE CLIENTES
# ============================================================

def generar_tabla_clientes(num_clientes):
    """Genera la tabla completa de clientes"""
    clientes = []
    
    print(f"Generando {num_clientes} clientes...")
    
    for i in range(1, num_clientes + 1):
        # Generar datos del cliente
        nombre = fake.name()
        email = generar_email(nombre)
        
        # Ciudad con barrio
        ciudad = f"{random.choice(BARRIOS_BA)}"
        
        fecha_alta = generar_fecha_alta()
        
        cliente = {
            'id_cliente': i,
            'nombre_cliente': nombre,
            'email': email,
            'ciudad': ciudad,
            'fecha_alta': fecha_alta.strftime('%Y-%m-%d')
        }
        
        clientes.append(cliente)
        
        if i % 100 == 0:
            print(f"  → {i} clientes generados...")
    
    print("✓ Generación completada!")
    return pd.DataFrame(clientes)


df_clientes = generar_tabla_clientes(NUM_CLIENTES)

df_clientes['fecha_alta'] = pd.to_datetime(df_clientes['fecha_alta'])

# ============================================================
# ESTADÍSTICAS DE CLIENTES
# ============================================================

print("\n" + "="*60)
print("ESTADÍSTICAS DE CLIENTES:")
print("="*60)
print(f"Total clientes: {len(df_clientes)}")
print(f"Ciudades únicas: {df_clientes['ciudad'].nunique()}")
print(f"\nDistribución por barrio:")
print(df_clientes['ciudad'].value_counts())
print(f"\nRango de fechas de registro:")
print(f"  Primera alta: {df_clientes['fecha_alta'].min()}")
print(f"  Última alta: {df_clientes['fecha_alta'].max()}")

print("\n" + "="*60)
print("MUESTRA DE CLIENTES:")
print("="*60)
print(df_clientes.head(10))

# ============================================================
# PERFILES DE COMPORTAMIENTO
# ============================================================

PERFILES_FRECUENCIA = {
    'unico': {
        'peso': 0.15,
        'compras_mes': 0,  # Solo la primera compra
    },
    'ocasional': {
        'peso': 0.25,
        'compras_mes': 0.4,
    },
    'regular': {
        'peso': 0.35,
        'compras_mes': 1.5,
    },
    'frecuente': {
        'peso': 0.20,
        'compras_mes': 6,
    },
    'vip': {
        'peso': 0.05,
        'compras_mes': 15,
    }
}

PERFILES_PAGO = {
    'tarjeta_preferente': {
        'peso': 0.40,
        'medios': {'tarjeta': 0.75, 'qr': 0.15, 'efectivo': 0.08, 'transferencia': 0.02}
    },
    'efectivo_preferente': {
        'peso': 0.30,
        'medios': {'efectivo': 0.70, 'tarjeta': 0.20, 'qr': 0.08, 'transferencia': 0.02}
    },
    'digital': {
        'peso': 0.20,
        'medios': {'qr': 0.60, 'transferencia': 0.25, 'tarjeta': 0.15, 'efectivo': 0.00}
    },
    'mixto': {
        'peso': 0.10,
        'medios': {'tarjeta': 0.40, 'efectivo': 0.30, 'qr': 0.20, 'transferencia': 0.10}
    }
}

PERFILES_TEMPORAL = {
    'trabajador_oficina': {
        'peso': 0.30,
        'dias': [0, 1, 2, 3, 4],  # Lun-Vie
        'horarios': [(12, 14), (18, 20)]
    },
    'del_barrio': {
        'peso': 0.25,
        'dias': [0, 1, 2, 3, 4, 5],  # Lun-Sab
        'horarios': [(9, 12), (17, 19)]
    },
    'familia_finde': {
        'peso': 0.20,
        'dias': [4, 5, 6],  # Vie-Dom
        'horarios': [(10, 13), (17, 20)]
    },
    'flexible': {
        'peso': 0.25,
        'dias': [0, 1, 2, 3, 4, 5, 6],  # Todos
        'horarios': [(8, 22)]
    }
}

FECHA_HOY = datetime(2024, 10, 31)
PROB_DOBLE_COMPRA_DIA = 0.05

# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def asignar_perfil(perfiles_dict):
    """Asigna un perfil basado en pesos probabilísticos"""
    perfiles = list(perfiles_dict.keys())
    pesos = [perfiles_dict[p]['peso'] for p in perfiles]
    return random.choices(perfiles, weights=pesos, k=1)[0]

def elegir_medio_pago(perfil_pago):
    """Elige medio de pago según perfil del cliente"""
    medios = list(PERFILES_PAGO[perfil_pago]['medios'].keys())
    pesos = list(PERFILES_PAGO[perfil_pago]['medios'].values())
    return random.choices(medios, weights=pesos, k=1)[0]

def generar_fecha_venta(fecha_inicio, fecha_fin, perfil_temporal):
    """Genera fecha con día y hora según perfil temporal"""
    dias_activos = PERFILES_TEMPORAL[perfil_temporal]['dias']
    horarios = PERFILES_TEMPORAL[perfil_temporal]['horarios']
    
    # Generar fecha aleatoria en el rango
    dias_diferencia = (fecha_fin - fecha_inicio).days
    if dias_diferencia <= 0:
        fecha = fecha_inicio
    else:
        fecha = fecha_inicio + timedelta(days=random.randint(0, dias_diferencia))
    
    # Ajustar al día de la semana permitido
    intentos = 0
    while fecha.weekday() not in dias_activos and intentos < 30:
        fecha += timedelta(days=1)
        if fecha > fecha_fin:
            fecha = fecha_inicio
        intentos += 1
    
    # Asignar hora según horarios pico
    rango_horario = random.choice(horarios)
    hora = random.randint(rango_horario[0], rango_horario[1])
    minuto = random.randint(0, 59)
    
    return fecha.replace(hour=hora, minute=minuto, second=0)

# ============================================================
# GENERACIÓN DE VENTAS
# ============================================================

def generar_ventas_cliente(cliente, perfil_frecuencia, perfil_pago, perfil_temporal):
    """Genera todas las ventas de un cliente según sus perfiles"""
    ventas = []
    
    fecha_alta = cliente['fecha_alta']
    meses_activo = (FECHA_HOY - fecha_alta).days / 30
    
    # Primera venta OBLIGATORIA en fecha_alta (o muy cerca)
    primera_venta = {
        'id_cliente': cliente['id_cliente'],
        'fecha': fecha_alta + timedelta(hours=random.randint(0, 48)),
        'nombre_cliente': cliente['nombre_cliente'],
        'email': cliente['email'],
        'medio_pago': elegir_medio_pago(perfil_pago)
    }
    ventas.append(primera_venta)
    
    # Generar ventas adicionales según frecuencia
    compras_mes = PERFILES_FRECUENCIA[perfil_frecuencia]['compras_mes']
    num_ventas_adicionales = int(meses_activo * compras_mes)
    
    for _ in range(num_ventas_adicionales):
        fecha_venta = generar_fecha_venta(fecha_alta, FECHA_HOY, perfil_temporal)
        
        venta = {
            'id_cliente': cliente['id_cliente'],
            'fecha': fecha_venta,
            'nombre_cliente': cliente['nombre_cliente'],
            'email': cliente['email'],
            'medio_pago': elegir_medio_pago(perfil_pago)
        }
        ventas.append(venta)
    
    # Casos especiales: 5% de clientes frecuentes compran 2 veces el mismo día
    if perfil_frecuencia in ['frecuente', 'vip'] and random.random() < PROB_DOBLE_COMPRA_DIA:
        if len(ventas) > 1:
            venta_duplicar = random.choice(ventas[1:])  # No duplicar la primera
            venta_doble = venta_duplicar.copy()
            # Cambiar hora (ej: mañana y tarde)
            hora_nueva = (venta_duplicar['fecha'].hour + random.randint(4, 8)) % 24
            venta_doble['fecha'] = venta_duplicar['fecha'].replace(hour=hora_nueva)
            ventas.append(venta_doble)
    
    return ventas

def generar_tabla_ventas():
    """Genera tabla completa de ventas"""
    todas_ventas = []
    
    print(f"Generando ventas para {len(df_clientes)} clientes...")
    
    for idx, cliente in df_clientes.iterrows():
        # Asignar perfiles al cliente
        perfil_frec = asignar_perfil(PERFILES_FRECUENCIA)
        perfil_pago = asignar_perfil(PERFILES_PAGO)
        perfil_temp = asignar_perfil(PERFILES_TEMPORAL)
        
        # Generar ventas del cliente
        ventas_cliente = generar_ventas_cliente(
            cliente, perfil_frec, perfil_pago, perfil_temp
        )
        todas_ventas.extend(ventas_cliente)
        
        if (idx + 1) % 100 == 0:
            print(f"  → {idx + 1} clientes procesados...")
    
    # Convertir a DataFrame
    df_ventas = pd.DataFrame(todas_ventas)
    
    # Ordenar por fecha
    df_ventas = df_ventas.sort_values('fecha').reset_index(drop=True)
    
    # Asignar IDs de venta
    df_ventas.insert(0, 'id_venta', range(1, len(df_ventas) + 1))
    
    # Formatear fecha
    df_ventas['fecha'] = df_ventas['fecha'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    print("✓ Generación completada!")
    return df_ventas


df_ventas = generar_tabla_ventas()

# ============================================================
# ESTADÍSTICAS DE VENTAS
# ============================================================

print("\n" + "="*60)
print("ESTADÍSTICAS DE VENTAS:")
print("="*60)
print(f"Total ventas generadas: {len(df_ventas)}")
print(f"Promedio ventas por cliente: {len(df_ventas) / len(df_clientes):.1f}")
print(f"\nDistribución por medio de pago:")
print(df_ventas['medio_pago'].value_counts())
print(f"\nRango de fechas:")
print(f"  Primera venta: {df_ventas['fecha'].min()}")
print(f"  Última venta: {df_ventas['fecha'].max()}")

print("\n" + "="*60)
print("MUESTRA DE VENTAS:")
print("="*60)
print(df_ventas.head(15))

# ============================================================
# CARGAR PRODUCTOS Y ASIGNAR POPULARIDAD
# ============================================================

# Cargar productos desde Excel
df_productos = pd.read_excel(r"C:\Users\renzo\OneDrive\Escritorio\BD_Proyecto_Aurelion\Productos.xlsx")

def asignar_popularidad(df_productos):
    """Asigna nivel de popularidad a cada producto según criterios"""
    df = df_productos.copy()
    
    # Crear score de popularidad
    df['score_pop'] = 0
    
    # +3 puntos: Productos básicos esenciales
    nombres_basicos = ['Coca', 'Agua', 'Leche', 'Pan', 'Yerba', 'Café']
    for nombre in nombres_basicos:
        df.loc[df['nombre_producto'].str.contains(nombre, case=False, na=False), 'score_pop'] += 3
    
    # +2 puntos: Precio bajo (<2000)
    df.loc[df['precio_unitario'] < 2000, 'score_pop'] += 2
    
    # +1 punto: Precio medio (2000-3500)
    df.loc[(df['precio_unitario'] >= 2000) & (df['precio_unitario'] < 3500), 'score_pop'] += 1
    
    # +1 punto: Es Alimento
    df.loc[df['categoria'] == 'Alimentos', 'score_pop'] += 1
    
    # -1 punto: Precio alto (>4500)
    df.loc[df['precio_unitario'] > 4500, 'score_pop'] -= 1
    
    # Ordenar por score
    df = df.sort_values('score_pop', ascending=False).reset_index(drop=True)
    
    # Asignar niveles de popularidad
    df.loc[0:9, 'popularidad'] = 'estrella'      # Top 10
    df.loc[10:29, 'popularidad'] = 'alta'        # 20 productos
    df.loc[30:59, 'popularidad'] = 'media'       # 30 productos
    df.loc[60:84, 'popularidad'] = 'baja'        # 25 productos
    df.loc[85:, 'popularidad'] = 'muy_baja'      # 15 productos
    
    return df

df_productos = asignar_popularidad(df_productos)

print("\n" + "="*60)
print("DISTRIBUCIÓN DE POPULARIDAD DE PRODUCTOS:")
print("="*60)
print(df_productos['popularidad'].value_counts().sort_index())
print("\n10 Productos más populares:")
print(df_productos[['nombre_producto', 'categoria', 'precio_unitario', 'popularidad']].head(10))

# ============================================================
# CONFIGURACIÓN DE TIPOS DE COMPRA
# ============================================================

TIPOS_COMPRA = {
    'rapida_snack': {
        'peso': 0.30,
        'num_productos': (1, 3),
        'monto_min': 500,
        'monto_max': 2000,
    },
    'diaria_basica': {
        'peso': 0.40,
        'num_productos': (3, 8),
        'monto_min': 2000,
        'monto_max': 5000,
    },
    'semanal': {
        'peso': 0.25,
        'num_productos': (8, 15),
        'monto_min': 5000,
        'monto_max': 12000,
    },
    'grande_mensual': {
        'peso': 0.05,
        'num_productos': (15, 25),
        'monto_min': 12000,
        'monto_max': 25000,
    }
}

# Probabilidades de selección por popularidad
PROB_SELECCION = {
    'estrella': 0.45,
    'alta': 0.30,
    'media': 0.15,
    'baja': 0.08,
    'muy_baja': 0.02
}

# ============================================================
# FUNCIONES DE GENERACIÓN
# ============================================================

def determinar_tipo_compra(medio_pago):
    """Determina tipo de compra, influenciado por medio de pago"""
    # Efectivo tiende a compras pequeñas
    if medio_pago == 'efectivo':
        pesos_ajustados = [0.50, 0.40, 0.08, 0.02]
    # Transferencia tiende a compras grandes
    elif medio_pago == 'transferencia':
        pesos_ajustados = [0.10, 0.30, 0.40, 0.20]
    # Otros medios: distribución normal
    else:
        pesos_ajustados = [v['peso'] for v in TIPOS_COMPRA.values()]
    
    tipos = list(TIPOS_COMPRA.keys())
    return random.choices(tipos, weights=pesos_ajustados, k=1)[0]

def seleccionar_producto_por_popularidad():
    """Selecciona un producto respetando probabilidades de popularidad"""
    popularidades = list(PROB_SELECCION.keys())
    probs = list(PROB_SELECCION.values())
    
    popularidad_elegida = random.choices(popularidades, weights=probs, k=1)[0]
    productos_disponibles = df_productos[df_productos['popularidad'] == popularidad_elegida]
    
    if len(productos_disponibles) > 0:
        return productos_disponibles.sample(1).iloc[0]
    else:
        return df_productos.sample(1).iloc[0]

def calcular_cantidad(precio_unitario):
    """Calcula cantidad realista según el precio del producto"""
    if precio_unitario < 2000:
        return random.randint(1, 4)  # Productos baratos: más cantidad
    elif precio_unitario < 4000:
        return random.randint(1, 3)  # Productos medios
    else:
        return random.randint(1, 2)  # Productos caros: menos cantidad

def generar_detalle_venta(venta, tipo_compra):
    """Genera el detalle completo de una venta"""
    config = TIPOS_COMPRA[tipo_compra]
    num_productos = random.randint(config['num_productos'][0], config['num_productos'][1])
    
    detalles = []
    productos_seleccionados = set()
    
    for _ in range(num_productos):
        # Seleccionar producto (evitar duplicados en misma venta)
        intentos = 0
        while intentos < 10:
            producto = seleccionar_producto_por_popularidad()
            if producto['id_producto'] not in productos_seleccionados:
                productos_seleccionados.add(producto['id_producto'])
                break
            intentos += 1
        
        # Si no encontró único, usar el último
        cantidad = calcular_cantidad(producto['precio_unitario'])
        importe = cantidad * producto['precio_unitario']
        
        detalle = {
            'id_venta': venta['id_venta'],
            'id_producto': producto['id_producto'],
            'nombre_producto': producto['nombre_producto'],
            'cantidad': cantidad,
            'precio_unitario': producto['precio_unitario'],
            'importe': importe
        }
        detalles.append(detalle)
    
    return detalles

df_detalle_nuevo = generar_tabla_detalle_ventas_mejorada(df_ventas, df_productos)

# 3. Validar calidad
validar_detalle_ventas(df_detalle_nuevo, df_ventas)

# ============================================================
# EXPORTACIÓN DE TABLAS A ESCRITORIO
# ============================================================

# Ruta de destino
ruta_escritorio = r"C:\Users\renzo\OneDrive\Escritorio"

# Crear carpeta para el proyecto (opcional)
carpeta_proyecto = os.path.join(ruta_escritorio, "BD_Aurelion")
os.makedirs(carpeta_proyecto, exist_ok=True)

print("\n" + "="*60)
print("EXPORTANDO TABLAS...")
print("="*60)

# Exportar Clientes
archivo_clientes = os.path.join(carpeta_proyecto, "Clientes.csv")
df_clientes.to_csv(archivo_clientes, index=False, encoding='utf-8-sig')
print(f"✓ Clientes exportados: {archivo_clientes}")

# Exportar Productos (con popularidad agregada)
archivo_productos = os.path.join(carpeta_proyecto, "Productos.csv")
df_productos.to_csv(archivo_productos, index=False, encoding='utf-8-sig')
print(f"✓ Productos exportados: {archivo_productos}")

# Exportar Ventas
archivo_ventas = os.path.join(carpeta_proyecto, "Ventas.csv")
df_ventas.to_csv(archivo_ventas, index=False, encoding='utf-8-sig')
print(f"✓ Ventas exportadas: {archivo_ventas}")

# Exportar Detalle_Ventas
archivo_detalle = os.path.join(carpeta_proyecto, "Detalle_Ventas.csv")
df_detalle_nuevo.to_csv(archivo_detalle, index=False, encoding='utf-8-sig')
print(f"✓ Detalle_Ventas exportado: {archivo_detalle}")

print("\n" + "="*60)
print("RESUMEN DE EXPORTACIÓN:")
print("="*60)
print(f"Carpeta destino: {carpeta_proyecto}")
print(f"\nArchivos generados:")
print(f"  - Clientes.csv ({len(df_clientes)} registros)")
print(f"  - Productos.csv ({len(df_productos)} registros)")
print(f"  - Ventas.csv ({len(df_ventas)} registros)")
print(f"  - Detalle_Ventas.csv ({len(df_detalle_nuevo)} registros)")
print("\n✓ Exportación completada exitosamente!")