import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from PIL import Image, ImageTk
from tkcalendar import DateEntry
import os



icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
db_path = "academia.db"

def validate_Database(file_path):
    if os.path.exists(file_path):
        return True
    else:
        with open(file_path, 'w') as f:
            pass
        db = Database(file_path)
        db.create_tables()
        return True


class Database:
    def __init__(self, path=None):
        self.path = path if path else db_path
        self.conn = sqlite3.connect(self.path)
        self.cursor = self.conn.cursor()
        self.create_tables()
        
        
    def create_tables(self):
        self.query("""
            CREATE TABLE IF NOT EXISTS "curso" (
                "id"	VARCHAR(15) UNIQUE,
                "nombre"	VARCHAR(100),
                "docente_id"	INTEGER,
                PRIMARY KEY("id")
            );""")
        self.query("""
            CREATE TABLE IF NOT EXISTS "docente" (
                "id"	VARCHAR(15) UNIQUE,
                "dni"	TEXT UNIQUE,
                "apellido"	TEXT NOT NULL,
                "nombre"	TEXT NOT NULL,
                "especialidad"	TEXT,
                "celular"	TEXT,
                "email"	TEXT,
                PRIMARY KEY("id")
            );""")
        self.query("""
            CREATE TABLE IF NOT EXISTS "estudiante" (
                "id"	VARCHAR(15) UNIQUE,
                "dni"	TEXT NOT NULL UNIQUE,
                "apellido"	TEXT NOT NULL,
                "nombre"	TEXT NOT NULL,
                "grado"	TEXT,
                "fecha_nacimiento"	date,
                "area"	TEXT,
                "celular"	TEXT,
                "direccion"	TEXT,
                PRIMARY KEY("id")
            );""")
        self.query("""    
            CREATE TABLE IF NOT EXISTS "grado" (
                "id"	VARCHAR(15) UNIQUE,
                "nombre"	VARCHAR(255) NOT NULL,
                PRIMARY KEY("id")
            );""")
        self.query("""    
            CREATE TABLE IF NOT EXISTS "notas" (
                "id"	INTEGER,
                "id_estudiante"	INTEGER,
                "id_curso"	INTEGER,
                "tipo"	TEXT NOT NULL,
                "valor"	REAL NOT NULL,
                "fecha"	DATE NOT NULL,
                "comentarios"	TEXT,
                PRIMARY KEY("id" AUTOINCREMENT),
                FOREIGN KEY("id_curso") REFERENCES "curso"("id"),
                FOREIGN KEY("id_estudiante") REFERENCES "estudiante"("id")
            );  
                   """)
        
        self.query("""
            CREATE TABLE IF NOT EXISTS "matricula" (
                "id"	INTEGER,
                "id_estudiante"	VARCHAR(15),
                "id_curso"	VARCHAR(15),
                PRIMARY KEY("id" AUTOINCREMENT)
)
                   """)

    def query(self, query, params=(), fetch=False):
        try:
            self.cursor.execute(query, params)
            if fetch:
                return self.cursor.fetchall()
            else:
                self.conn.commit()
        except sqlite3.DatabaseError as e:
            messagebox.showerror("Database Error", f"Database error ocurred:\n{e}")     
            return None   
        
        except Exception as e:
            messagebox.showerror("Error", f"Error en consulta: {e}")
        return []

    def get_data_table(self, table_name, order_by="id", query=None):
        if not query and table_name != "edit":
            if table_name == 'curso':
                query1 = f"SELECT c.id,c.nombre as curso, d.nombre || ' ' || d.apellido as docente FROM curso c LEFT JOIN docente d ON c.docente_id = d.id"
            elif table_name == 'matricula':
                print(order_by)
                query1 = f"SELECT m.id, e.nombre || ' ' || e.apellido as estudiante, c.nombre as curso FROM matricula m LEFT JOIN estudiante e ON m.id_estudiante = e.id LEFT JOIN curso c ON m.id_curso = c.id ORDER BY m.id"
            else:
                query1 = f"SELECT * FROM {table_name} ORDER BY {order_by}"
        else:
            
            query1 = query
        data = self.query(query1, fetch=True)
        headers = [d[0] for d in self.cursor.description]
        return headers, data

    def close(self):
        self.conn.close()
        
class Elemento:
    
    _tipos_cache = {}
    def __init__(self, tipo):
        self.db = Database()
        self.tipo = tipo
        if tipo not in Elemento._tipos_cache:
            Elemento._tipos_cache[tipo] = self.db.get_data_table(tipo)[0]
        self.lista_tipos = Elemento._tipos_cache
        self.lista_tipos_default = self.lista_tipos.copy()
        
    def return_data(self):
        return self.lista_tipos[self.tipo]

    def validate_tipo(self, tipo):
        if tipo == "curso":
            self.lista_tipos[tipo] = ['id', 'nombre', 'docente_id']
        elif tipo == "matricula":
            self.lista_tipos[tipo] = ['id', 'id_estudiante', 'id_curso']

    def insert_elementDB(self, data):
        print("Insert")
        self.validate_tipo(self.tipo)
        query = f"INSERT INTO {self.tipo} ({', '.join(self.lista_tipos[self.tipo])}) VALUES ({', '.join(['?' for _ in self.lista_tipos[self.tipo]])})"
        self.db.query(query, data)
        
        self.lista_tipos = self.lista_tipos_default.copy()

    def update_elementDB(self, data, record_id):
        print("Update")
        self.validate_tipo(self.tipo)
        fields = self.lista_tipos[self.tipo]
        set_clause = ', '.join([f"{field}=?" for field in fields])
        query = f"UPDATE {self.tipo} SET {set_clause} WHERE id=?"
        self.db.query(query, data + [record_id])

        self.lista_tipos = self.lista_tipos_default.copy()

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Academia Celer")
        self.geometry("1300x700")
        icon_image = Image.open(icon_path)
        icon_photo = ImageTk.PhotoImage(icon_image)
        self.iconphoto(False, icon_photo)
        #self.resizable(0, 0)

        try: 
            self.DB = Database()
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")

        self.sidebarFrame = tk.Frame(self, width=250)
        self.sidebarFrame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebarFrame.pack_propagate(False)

        self.content_frame = tk.Frame(self)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.header_frame = tk.Frame(self.content_frame)
        self.header_frame.pack(side=tk.TOP, fill=tk.X)

        self.table_frame = tk.Frame(self.content_frame)
        self.table_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.createTitle(self.sidebarFrame)

        self.buttonList = {
            'Principal': self.showDashboard,
            'Estudiantes': lambda: self.showSection('estudiante'),
            'Cursos': lambda: self.showSection('curso'),
            'Docentes': lambda: self.showSection('docente'),
            'Grados': lambda: self.showSection('grado'),
            'Matriculas': lambda: self.showSection('matricula'),
            'Notas': lambda: self.showSection('notas'),
            'Avanzado': lambda: self.open_SQL_editor()
            
        }
        
        self.elementos = {
            'estudiante': Elemento('estudiante'),
            'curso': Elemento('curso'),
            'docente': Elemento('docente'),
            'grado': Elemento('grado'),
            'notas': Elemento('notas'),
            'matricula': Elemento('matricula')
        }
        self.createButtons(self.sidebarFrame, self.buttonList)
        self.showDashboard()

        self.bind("q", lambda e: self.destroy())

    def open_SQL_editor(self):
        window = tk.Toplevel(self)
        
        
        consulta_examples = {
"1. Cursos con docente asignado": 
'''
SELECT 
    curso.id AS curso_id,
    curso.nombre AS curso_nombre,
    docente.nombre || ' ' || docente.apellido AS docente
FROM curso
JOIN docente ON curso.docente_id = docente.id;''',

"2. Estudiantes por curso (cambia CURSO123)": 
'''
SELECT 
    curso.nombre AS curso,
    estudiante.nombre || ' ' || estudiante.apellido AS estudiante
FROM matricula
JOIN curso ON matricula.id_curso = curso.id
JOIN estudiante ON matricula.id_estudiante = estudiante.id
WHERE curso.id = 'CURSO123';''',

"3. Notas por estudiante (cambia EST123)": 
'''
SELECT 
    estudiante.nombre || ' ' || estudiante.apellido AS estudiante,
    curso.nombre AS curso,
    notas.tipo,
    notas.valor,
    notas.fecha
FROM notas
JOIN estudiante ON notas.id_estudiante = estudiante.id
JOIN curso ON notas.id_curso = curso.id
WHERE estudiante.id = 'EST123';'''
            }

        def insert_sql(event):
            selection = combo.get()
            query_entry.delete("1.0", tk.END)
            query_entry.insert(tk.END, consulta_examples[selection])
        
        tk.Label(window, text="Consultas predefinidas").pack()
        combo = ttk.Combobox(window, values=list(consulta_examples.keys()), width=40, state="readonly")
        combo.pack()
        combo.bind("<<ComboboxSelected>>", insert_sql)
        
        tk.Label(window, text="Ejecutar SQL").pack()
        
        # Area de texto para el SQL
        query_entry = tk.Text(window, width=100, height=10)
        query_entry.pack()
        query_entry.bind("<Alt-Key-q>", lambda: mostrar_sql())
        
        # Boton Ejecutar
        execute_btn = tk.Button(window, text="Ejecutar Consulta", command=lambda : mostrar_sql())
        execute_btn.pack()
        
        def mostrar_sql():
            table_window = tk.Toplevel(window)
            text = query_entry.get("1.0", tk.END)
        
            try:
                table_data = self.DB.get_data_table(table_name="edit",query=text)
                self.createTable(table_data[0], table_data[1], parent=table_window)
            except Exception as e:
                error_win = tk.Toplevel(window)
                tk.Label(error_win, text=f"Error: {e}", fg="red").pack()
                             

    def createTitle(self, parent):
        title = tk.Label(parent, text='Academia Celer')
        image = Image.open(icon_path)
        image = image.resize((200, 200), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        image_label = tk.Label(parent, image=photo)
        image_label.image = photo
        image_label.pack(pady=(10, 0))
        title.pack(pady=20)

    def createButtons(self, parent, buttons: dict):
        for label, command in buttons.items():
            btn = tk.Button(parent, text=label, height=2, width=22, command=command)
            btn.pack(pady=5, padx=5)

    def select_database_file(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de base de datos",
            filetypes=[("Archivos SQLite", "*.db"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.DB = Database(file_path)
            self.DB.create_tables()            
            messagebox.showinfo("Éxito", "Base de datos seleccionada correctamente")
        return self.DB

    def showDashboard(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        select_db_btn = tk.Button(
            self.table_frame,
            text="Seleccionar BD",
            command = self.select_database_file
        )
        select_db_btn.pack(pady=20)

    def showSection(self, tipo):
        try:
            self.current_table = tipo
            self.current_elemento = self.elementos[tipo]

            for widget in self.header_frame.winfo_children():
                widget.destroy()

            if tipo == "no":
                for widget in self.table_frame.winfo_children():
                    widget.destroy()
                self.show_scores()
            
            
            else: 
                add_btn = tk.Button(
                    self.header_frame,
                    text=f'+ Agregar {tipo.capitalize()}',
                    command=lambda: self._open_form_window(tipo)
                )
                add_btn.grid(row=0, column=0, padx=10, pady=10)

                
                if 1:#tipo != "matricula":                
                    tk.Label(self.header_frame, text="Ordenar por:").grid(row=0, column=1, padx=10, pady=10)
                    vals = self.DB.get_data_table(tipo)[0]
                    vals = [val.replace("_", " ").upper() for val in vals]
                    sort_btn = ttk.Combobox(self.header_frame, values = vals, state="readonly")
                    sort_btn.set("ID")
                    sort_btn.grid(row=0, column=2, padx=1, pady=10)
                    sort_btn.bind("<<ComboboxSelected>>", lambda event: self.showTable(tipo, sort_btn.get().lower().replace(" ", "_")))
                
            
                self.showTable(tipo)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al mostrar la sección: \n{e}\n\nIntente cargar el archivo de la base de datos")

    def showTable(self, table_name, order_by="id"):
        headers_data = self.DB.get_data_table(table_name, order_by)
        headers = [header for header in headers_data[0]]
        data = headers_data[1]

        for widget in self.table_frame.winfo_children():
            widget.destroy()

        self.createTable(headers, data)

    def createTable(self, headers, data, parent=None):
        edit_state = False
        if not parent:
            parent = self.table_frame
            edit_state = True
            
            
        headers_display = [head.replace('_', ' ').upper() for head in headers]
        tree = ttk.Treeview(parent, columns=headers_display, show='headings', height=20)

        for header in headers_display:
            tree.heading(header, text=header)
            tree.column(header, anchor=tk.CENTER, width=150)

        for row in data:
            tree.insert('', tk.END, values=row)

        
        if edit_state:
            def on_double_click(event):
                item = tree.selection()
                if item:
                    row_data = tree.item(item)['values']
                    self._open_form_window(self.current_table, row_data, row_data[0])
                    
            def on_right_click(event):  
                selected_item = tree.identify_row(event.y)
                if selected_item:
                    tree.selection_set(selected_item)
                    row_data = tree.item(selected_item)['values']
                    record_id = row_data[0]
                    
                    context_menu = tk.Menu(tree, tearoff=0)
                    context_menu.add_command(label="Editar  ", command=lambda: self._open_form_window(self.current_table, row_data, record_id))
                    context_menu.add_command(label="Eliminar", command=lambda: self._delete_record(self.current_table, record_id))
                    context_menu.post(event.x_root, event.y_root)
                

            tree.bind("<Double-1>", on_double_click)
            tree.bind("<Button-3>", on_right_click)
        
        
        tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscroll=scrollbar_y.set, xscroll=scrollbar_x.set)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        

    def _open_form_window(self, tipo, data=None, record_id=None):
        elemento = self.elementos[tipo]
        campos = elemento.return_data()

        window = tk.Toplevel(self)
        window.title(f"{'Editar' if data else 'Agregar'} {tipo.capitalize()}")
        window.resizable(0, 0)
        form_frame = tk.Frame(window)
        btns_frame = tk.Frame(window, )

        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        btns_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20, anchor="center", side="bottom")

        entries = {}
        
        for idx, field in enumerate(campos):
            
            tk.Label(form_frame, text=field.replace("_"," ").upper(), width=15, justify="right", anchor="e").grid(row=idx, column=0, sticky=tk.W, pady=5)

            if field == "id":
                input_widget = tk.Entry(form_frame, width=30)
                input_widget.delete(0, tk.END)
                
                if not data:
                    next_id = self.get_next_id(tipo)
                    print(f"Insertando nuevo 'id': {next_id}")
                    input_widget.insert(0, next_id)
                    input_widget.config(state="readonly")

    
            elif field in ['grado', 'area']:
                if field == 'area':
                    values = [f"Area {i}" for i in ["I", "II", "III", "IV", "V"]]
                    
                    input_widget = ttk.Combobox(form_frame, values=values, state="readonly", width=27)
                    
                    if data:
                        input_widget.set(self.DB.query("SELECT area FROM estudiante WHERE id=?", (record_id,), fetch=True)[0][0])
                    else:
                        input_widget.set("")                 
                               
                elif field == 'grado':
                    values = self.DB.query("SELECT nombre FROM grado", fetch=True)
                    values = [item[0] for item in values] if values else ["None"]
                    input_widget = ttk.Combobox(form_frame, values=values, state="readonly", width=27)
        
                    if data:
                        input_widget.set(self.DB.query("SELECT grado FROM estudiante WHERE id=?", (record_id,), fetch=True)[0][0])
                    else:
                        input_widget.set(values[0])
                        
            # Asignar cursos a docentes
            elif field == 'docente' and tipo == 'curso':
                values = self.DB.query("SELECT id || '-' || nombre || ' ' || apellido FROM docente", fetch=True)    
                values = [v[0] for v in values]
                input_widget = ttk.Combobox(form_frame, values=values)
                
            elif tipo == "matricula":

                if field == "estudiante":
                    values = self.DB.query("SELECT id || '-' || nombre || ' ' || apellido FROM estudiante", fetch=True)
                    values = [v[0] for v in values]
                    input_widget = ttk.Combobox(form_frame, values=values, width=27)
                    
                elif field == "curso":
                    values = self.DB.query("SELECT id || '-' || nombre FROM curso", fetch=True)
                    values = [v[0] for v in values]
                    input_widget = ttk.Combobox(form_frame, values=values, width=27)
                
            
            else:
                input_widget = tk.Entry(form_frame, width=30)

            input_widget.grid(row=idx, column=1, pady=5, padx=10)
            entries[field] = input_widget

            if data:
                
                input_widget.insert(0, data[idx])

        def save():
            form_data = [entries[field].get() for field in campos]
            if tipo == 'curso':    
                form_data[2] = form_data[2][:form_data[2].index('-')]
                
            if tipo == 'matricula':
                
                form_data[1] = form_data[1][:form_data[1].index('-')]
                form_data[2] = form_data[2][:form_data[2].index('-')]
                
            if any(form_data):
                if record_id:
                    elemento.update_elementDB(form_data, record_id)
                    messagebox.showinfo("Actualizado", f"{tipo.capitalize()} actualizado")
                else:
                    elemento.insert_elementDB(form_data)
                    messagebox.showinfo("Éxito", f"{tipo.capitalize()} agregado")
                window.destroy()
                self.showTable(tipo)
            else:
                messagebox.showerror("Error", "Complete todos los campos")

        window.bind("<Return>", lambda event: save())

        tk.Button(btns_frame, text="Guardar", width=10, command=save, anchor="center").grid(row=0, column=0, pady=10, padx=40)
        tk.Button(btns_frame, text="Cancelar", width=10, command=window.destroy, anchor="center").grid(row=0, column=1, pady=10, padx=40)
        window.protocol("WM_DELETE_WINDOW", window.destroy)
    
    def get_next_id(self, tipo):
        print(tipo)
        max_id = self.DB.query(f"SELECT MAX(id) FROM {tipo}", fetch=True)[0][0]
        if tipo not in ["matricula", "notas"]:
            lim = 3
            prefix = tipo[0].upper()
            return f"{prefix}{str(int(max_id[1:]) + 1).zfill(lim)}" if max_id else f"{prefix}{'1'.zfill(lim)}"
        else:
            return str(int(max_id) + 1) if max_id else "1"
        
        
    def show_scores(self):
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        filter_frame = tk.Frame(self.table_frame)
        filter_frame.pack(pady=10)

        # Filtros
        tk.Label(filter_frame, text="Grado:").grid(row=0, column=0, padx=5)
        grades = self.DB.query("SELECT DISTINCT grado FROM estudiante", fetch=True)
        grades = [g[0] for g in grades if g[0]]
        grado_cb = ttk.Combobox(filter_frame, values=grades, state="readonly", width=20)
        grado_cb.grid(row=0, column=1, padx=5)

        tk.Label(filter_frame, text="Estudiante:").grid(row=0, column=2, padx=5)
        students = self.DB.query("SELECT id || '-' || nombre || ' ' || apellido FROM estudiante", fetch=True)
        student_cb = ttk.Combobox(filter_frame, values=[s[0] for s in students], width=30)
        student_cb.grid(row=0, column=3, padx=5)

        tk.Label(filter_frame, text="Curso:").grid(row=0, column=4, padx=5)
        cursos = self.DB.query("SELECT id || '-' || nombre FROM curso", fetch=True)
        curso_cb = ttk.Combobox(filter_frame, values=[c[0] for c in cursos], width=30)
        curso_cb.grid(row=0, column=5, padx=5)

        # Botón de aplicar filtros
        filter_btn = tk.Button(filter_frame, text="Aplicar", command=lambda: mostrar_notas())
        filter_btn.grid(row=0, column=6, padx=10)

        # Botón para agregar nota
        add_btn = tk.Button(filter_frame, text="+ Agregar Nota", command=lambda: self._open_form_nota())
        add_btn.grid(row=0, column=7, padx=10)

        table_container = tk.Frame(self.table_frame)
        table_container.pack(fill=tk.BOTH, expand=True)

        def mostrar_notas():
            for widget in table_container.winfo_children():
                widget.destroy()

            query = """
            SELECT 
                notas.id,
                estudiante.nombre || ' ' || estudiante.apellido AS estudiante,
                curso.nombre AS curso,
                notas.tipo,
                notas.valor,
                notas.fecha,
                notas.comentarios
            FROM notas
            JOIN estudiante ON notas.id_estudiante = estudiante.id
            JOIN curso ON notas.id_curso = curso.id
            WHERE 1=1
            """

            filters = []
            params = []

            if grado_cb.get():
                filters.append("estudiante.grado = ?")
                params.append(grado_cb.get())

            if student_cb.get():
                student_id = student_cb.get().split("-")[0]
                filters.append("estudiante.id = ?")
                params.append(student_id)

            if curso_cb.get():
                curso_id = curso_cb.get().split("-")[0]
                filters.append("curso.id = ?")
                params.append(curso_id)

            if filters:
                query += " AND " + " AND ".join(filters)

            data = self.DB.query(query, tuple(params), fetch=True)
            headers = ["ID", "Estudiante", "Curso", "Tipo", "Valor", "Fecha", "Comentarios"]
            self.createTable(headers, data, parent=table_container)

        mostrar_notas()
        
        
    def _delete_record(self, tipo, record_id):
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea eliminar este registro?"):
            l = self.DB.query(f"SELECT * FROM {tipo} WHERE id=?", (record_id,), fetch=True)
            l = " - ".join(l[0])
            if messagebox.askyesno("Confirmar", f"¿Realmente está seguro?\nSe eliminará:\n{l}"):
                self.DB.query(f"DELETE FROM {tipo} WHERE id=?", (record_id,))
                messagebox.showinfo("Eliminado", f"{tipo.capitalize()} eliminado")
                self.showTable(tipo)
                
    def destroy(self):
        self.DB.close()
        return super().destroy()

if __name__ == '__main__':
    if validate_Database(db_path):
        app = MainApp()
        app.mainloop()



