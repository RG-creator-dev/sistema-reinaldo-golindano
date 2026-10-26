import os 
for root, dirs, files in os.walk('.'): 
    for file in files: 
        if file.endswith(('.py', '.html', '.js')): 
            path = os.path.join(root, file) 
            try: 
                with open(path, 'r', encoding='utf-8') as f: content = f.read() 
                up = False 
                if "Entregado" in content or "archivar" in content.lower(): 
                    nc = content 
                    for viejo, nuevo in [("['Entregado']", "['Entregado', 'Cerrado', 'Reparado - Listo para Entrega']"), ('["Entregado"]', '["Entregado", "Cerrado", "Reparado - Listo para Entrega"]'), ("'Entregado', 'Cerrado'", "'Entregado', 'Cerrado', 'Reparado - Listo para Entrega'"), ('"Entregado", "Cerrado"', '"Entregado", "Cerrado", "Reparado - Listo para Entrega"')]: 
                        if viejo in nc: nc = nc.replace(viejo, nuevo); up = True 
                    if "No hay ¢rdenes cerradas" in nc: 
                        nc = nc.replace("No hay ¢rdenes cerradas (Entregado/Cerrado)", "No hay ¢rdenes para archivar"); up = True 
                    if up: 
                        with open(path, 'w', encoding='utf-8') as f: f.write(nc) 
                        print(f"[ACTUALIZADO] {path}") 
            except: pass 
