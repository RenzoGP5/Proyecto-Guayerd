# ============================================================
# VERSIÓN MEJORADA DE GENERACIÓN DE DETALLE_VENTAS
# ============================================================

import pandas as pd
import random

# Configuración (mantener igual)
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

PROB_SELECCION = {
    'estrella': 0.45,
    'alta': 0.30,
    'media': 0.15,
    'baja': 0.08,
    'muy_baja': 0.02
}

# ============================================================
# FUNCIONES MEJORADAS
# ============================================================

def determinar_tipo_compra(medio_pago):
    """Determina tipo de compra, influenciado por medio de pago"""
    if medio_pago == 'efectivo':
        pesos_ajustados = [0.50, 0.40, 0.08, 0.02]
    elif medio_pago == 'transferencia':
        pesos_ajustados = [0.10, 0.30, 0.40, 0.20]
    else:
        pesos_ajustados = [v['peso'] for v in TIPOS_COMPRA.values()]
    
    tipos = list(TIPOS_COMPRA.keys())
    return random.choices(tipos, weights=pesos_ajustados, k=1)[0]


def seleccionar_producto_por_popularidad(df_productos):
    """Selecciona un producto respetando probabilidades de popularidad"""
    popularidades = list(PROB_SELECCION.keys())
    probs = list(PROB_SELECCION.values())
    
    popularidad_elegida = random.choices(popularidades, weights=probs, k=1)[0]
    productos_disponibles = df_productos[df_productos['popularidad'] == popularidad_elegida]
    
    if len(productos_disponibles) > 0:
        return productos_disponibles.sample(1).iloc[0]
    else:
        return df_productos.sample(1).iloc[0]


def calcular_cantidad(precio_unitario, tipo_compra):
    """Calcula cantidad realista según precio Y tipo de compra"""
    
    # PRODUCTOS BARATOS (<$2000)
    if precio_unitario < 2000:
        if tipo_compra == 'rapida_snack':
            return random.randint(1, 2)
        elif tipo_compra == 'diaria_basica':
            return random.randint(1, 4)
        elif tipo_compra == 'semanal':
            return random.randint(2, 8)
        else:  # grande_mensual
            return random.randint(3, 12)
    
    # PRODUCTOS MEDIOS ($2000-$4000)
    elif precio_unitario < 4000:
        if tipo_compra in ['rapida_snack', 'diaria_basica']:
            return random.randint(1, 2)
        elif tipo_compra == 'semanal':
            return random.randint(1, 4)
        else:  # grande_mensual
            return random.randint(2, 6)
    
    # PRODUCTOS CAROS (>$4000)
    else:
        if tipo_compra in ['rapida_snack', 'diaria_basica']:
            return 1
        else:  # semanal o grande_mensual
            return random.randint(1, 3)


# ============================================================
# FUNCIÓN MEJORADA DE GENERACIÓN DE DETALLE
# ============================================================

def generar_detalle_venta_mejorado(venta, tipo_compra, df_productos):
    """
    Genera el detalle completo de una venta CON MEJORAS:
    
    1. ✅ Control de monto máximo
    2. ✅ Evita duplicados de forma robusta
    3. ✅ Agrega ID único a cada línea de detalle
    4. ✅ Genera precios históricos opcionales
    """
    config = TIPOS_COMPRA[tipo_compra]
    num_productos_objetivo = random.randint(config['num_productos'][0], config['num_productos'][1])
    
    detalles = []
    productos_seleccionados = set()
    total_acumulado = 0
    
    # Crear lista de productos disponibles para selección más eficiente
    productos_disponibles = df_productos.copy()
    
    for i in range(num_productos_objetivo):
        # Si quedan pocos productos disponibles, usar todos
        if len(productos_disponibles) == 0:
            break
        
        # Seleccionar producto (intentos limitados)
        producto = None
        intentos = 0
        max_intentos = 20  # Aumentado de 10 a 20
        
        while intentos < max_intentos:
            producto_candidato = seleccionar_producto_por_popularidad(productos_disponibles)
            
            if producto_candidato['id_producto'] not in productos_seleccionados:
                producto = producto_candidato
                productos_seleccionados.add(producto['id_producto'])
                break
            
            intentos += 1
        
        # Si después de max_intentos no encontró único, tomar uno aleatorio de los NO seleccionados
        if producto is None:
            productos_no_usados = productos_disponibles[
                ~productos_disponibles['id_producto'].isin(productos_seleccionados)
            ]
            
            if len(productos_no_usados) == 0:
                break  # No quedan productos únicos disponibles
            
            producto = productos_no_usados.sample(1).iloc[0]
            productos_seleccionados.add(producto['id_producto'])
        
        # Calcular cantidad y validar monto
        cantidad = calcular_cantidad(producto['precio_unitario'])
        
        # Opcional: Aplicar variación de precio histórico (5% de los productos)
        precio_unitario = producto['precio_unitario']
        if random.random() < 0.05:
            variacion = random.uniform(-0.10, 0.10)
            precio_unitario = round(precio_unitario * (1 + variacion), -1)
        
        importe = cantidad * precio_unitario
        
        # Control de monto máximo (con tolerancia del 10%)
        if total_acumulado + importe > config['monto_max'] * 1.1:
            # Ajustar cantidad para no exceder
            importe_disponible = config['monto_max'] * 1.1 - total_acumulado
            
            if importe_disponible < precio_unitario:
                # No cabe ni una unidad, terminar
                break
            
            cantidad = max(1, int(importe_disponible / precio_unitario))
            importe = cantidad * precio_unitario
        
        total_acumulado += importe
        
        detalle = {
            'id_venta': venta['id_venta'],
            'id_producto': int(producto['id_producto']),
            'nombre_producto': producto['nombre_producto'],
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'importe': importe
        }
        detalles.append(detalle)
        
        # Si alcanzó monto mínimo y ya tiene suficientes productos, puede terminar
        if total_acumulado >= config['monto_min'] and i >= config['num_productos'][0] - 1:
            if random.random() < 0.3:  # 30% chance de terminar antes
                break
    
    return detalles


# ============================================================
# FUNCIÓN PRINCIPAL DE GENERACIÓN
# ============================================================

def generar_tabla_detalle_ventas_mejorada(df_ventas, df_productos):
    """
    Genera tabla completa de detalle de ventas con mejoras
    """
    todos_detalles = []
    id_detalle_counter = 1  # Contador para ID único
    
    print(f"\n🔄 Generando detalles mejorados para {len(df_ventas)} ventas...")
    
    ventas_list = df_ventas.to_dict('records')
    
    for idx, venta in enumerate(ventas_list):
        # Determinar tipo de compra
        tipo_compra = determinar_tipo_compra(venta['medio_pago'])
        
        # Generar detalles con función mejorada
        detalles_venta = generar_detalle_venta_mejorado(venta, tipo_compra, df_productos)
        
        # Agregar ID único a cada detalle
        for detalle in detalles_venta:
            detalle['id_detalle'] = id_detalle_counter
            id_detalle_counter += 1
        
        todos_detalles.extend(detalles_venta)
        
        if (idx + 1) % 500 == 0:
            print(f"  → {idx + 1} ventas procesadas...")
    
    # Convertir a DataFrame
    df_detalle = pd.DataFrame(todos_detalles)
    
    # Reordenar columnas
    columnas_orden = ['id_detalle', 'id_venta', 'id_producto', 'nombre_producto', 
                      'cantidad', 'precio_unitario', 'importe']
    df_detalle = df_detalle[columnas_orden]
    
    print("✓ Generación completada!")
    return df_detalle


# ============================================================
# FUNCIONES DE VALIDACIÓN
# ============================================================

def validar_detalle_ventas(df_detalle, df_ventas):
    """
    Valida la calidad del detalle_ventas generado
    """
    print("\n" + "="*60)
    print("📊 VALIDACIÓN DE CALIDAD:")
    print("="*60)
    
    # 1. Verificar duplicados dentro de cada venta
    duplicados = df_detalle.groupby(['id_venta', 'id_producto']).size()
    duplicados = duplicados[duplicados > 1]
    
    if len(duplicados) > 0:
        print(f"⚠️  ADVERTENCIA: {len(duplicados)} productos duplicados en ventas")
        print(f"   Primeros duplicados encontrados:")
        print(duplicados.head())
    else:
        print("✅ Sin productos duplicados dentro de cada venta")
    
    # 2. Verificar distribución de productos por venta
    productos_por_venta = df_detalle.groupby('id_venta').size()
    
    print(f"\n📈 Distribución de productos por venta:")
    print(f"   Promedio: {productos_por_venta.mean():.1f} productos")
    print(f"   Mediana: {productos_por_venta.median():.0f} productos")
    print(f"   Mínimo: {productos_por_venta.min()} productos")
    print(f"   Máximo: {productos_por_venta.max()} productos")
    
    # 3. Verificar distribución por rangos
    print(f"\n📊 Ventas por rango de productos:")
    rango_1_3 = len(productos_por_venta[(productos_por_venta >= 1) & (productos_por_venta <= 3)])
    rango_4_8 = len(productos_por_venta[(productos_por_venta >= 4) & (productos_por_venta <= 8)])
    rango_9_15 = len(productos_por_venta[(productos_por_venta >= 9) & (productos_por_venta <= 15)])
    rango_16_25 = len(productos_por_venta[(productos_por_venta >= 16) & (productos_por_venta <= 25)])
    
    total_ventas = len(productos_por_venta)
    print(f"   1-3 productos:   {rango_1_3:>5} ventas ({rango_1_3/total_ventas*100:>5.1f}%) ← Esperado: ~30%")
    print(f"   4-8 productos:   {rango_4_8:>5} ventas ({rango_4_8/total_ventas*100:>5.1f}%)")
    print(f"   9-15 productos:  {rango_9_15:>5} ventas ({rango_9_15/total_ventas*100:>5.1f}%)")
    print(f"   16-25 productos: {rango_16_25:>5} ventas ({rango_16_25/total_ventas*100:>5.1f}%) ← Esperado: ~5%")
    
    # 4. Verificar montos
    totales_por_venta = df_detalle.groupby('id_venta')['importe'].sum()
    
    print(f"\n💰 Distribución de montos totales por venta:")
    print(f"   Promedio: ${totales_por_venta.mean():,.0f}")
    print(f"   Mediana: ${totales_por_venta.median():,.0f}")
    print(f"   Mínimo: ${totales_por_venta.min():,.0f}")
    print(f"   Máximo: ${totales_por_venta.max():,.0f}")
    
    return True


# ============================================================
# EJEMPLO DE USO
# ============================================================

if __name__ == "__main__":
    print("="*60)
    print("SCRIPT DE MEJORA PARA DETALLE_VENTAS")
    print("="*60)
    print("\nEste script incluye las siguientes mejoras:")
    print("  1. ✅ Control de monto máximo por tipo de compra")
    print("  2. ✅ Evita duplicados de forma robusta")
    print("  3. ✅ Agrega ID único (id_detalle) a cada línea")
    print("  4. ✅ Opción de precios históricos (5% de variación)")
    print("  5. ✅ Validación de calidad completa")
    print("\nPara usar:")
    print("  df_detalle = generar_tabla_detalle_ventas_mejorada(df_ventas, df_productos)")
    print("  validar_detalle_ventas(df_detalle, df_ventas)")