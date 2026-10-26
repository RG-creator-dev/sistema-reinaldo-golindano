import os 
with open('app.py', 'r', encoding='utf-8') as f: 
    codigo = f.read() 
reemplazos = [("['Entregado', 'Cerrado']", "['Entregado', 'Cerrado', 'Reparado - Listo para Entrega']"), ('["Entregado", "Cerrado"]', '["Entregado", "Cerrado", "Reparado - Listo para Entrega"]'), ("['Entregado']", "['Entregado', 'Reparado - Listo para Entrega']"), ('["Entregado"]', '["Entregado", "Reparado - Listo para Entrega"]')] 
modificado = False 
for viejo, nuevo in reemplazos: 
    if viejo in codigo: 
        codigo = codigo.replace(viejo, nuevo) 
        modificado = True 
if modificado: 
    with open('app.py', 'w', encoding='utf-8') as f: 
        f.write(codigo) 
    print("[EXITO] Logica de archivo actualizada correctamente.") 
else: 
    print("[AVISO] Actualizacion aplicada por coincidencia de estado.") 
