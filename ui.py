import os
import ctypes
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import Gtk, Gdk, GLib, Pango, Gio, GObject

from cpu import Memory, CPU
from assembler import Assembler


class ItemMenu(GObject.Object):
    __gtype_name__ = 'ItemMenu'

    def __init__(self, item_id, nombre):
        super().__init__()
        self._id = item_id
        self._nombre = nombre

    @GObject.Property(type=str)
    def item_id(self): return self._id

    @GObject.Property(type=str)
    def nombre(self): return self._nombre


class SimulatorWindow(Gtk.ApplicationWindow):
    def add_font(self, font):
        font_path = os.path.join(os.path.dirname(__file__), "fonts", f"{font}.ttf")

        if not os.path.exists(font_path):
            return False
            
        try:
            try:
                libfc = ctypes.CDLL("libfontconfig.so.1")
            except OSError:
                libfc = ctypes.CDLL("libfontconfig.so")
                
            libfc.FcConfigGetCurrent.restype = ctypes.c_void_p
            libfc.FcConfigAppFontAddFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            libfc.FcConfigAppFontAddFile.restype = ctypes.c_bool
            
            config_actual = libfc.FcConfigGetCurrent()
            libfc.FcConfigAppFontAddFile(config_actual, font_path.encode('utf-8'))
        except Exception:
            pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        ui_file = os.path.join(os.path.dirname(__file__), "window.ui")

        if os.path.exists(ui_file):
            builder = Gtk.Builder()
            builder.add_from_file(ui_file)

            window_obj = builder.get_object("main_window")
            main_window_content = window_obj.get_child()
            window_obj.set_child(None)
            self.set_child(main_window_content)

            self.lbl_regs = builder.get_object("lbl_regs")
            self.entry_key = builder.get_object("entry_key")
            self.display_view = builder.get_object("display_view")
            self.trace_view = builder.get_object("trace_view")
            self.mem_view = builder.get_object("mem_view")
            self.code_view = builder.get_object("code_view")
            self.frec_drop = builder.get_object("frec_drop")

            builder.get_object("btn_assemble").connect("clicked", self.on_assemble_clicked)
            builder.get_object("btn_step").connect("clicked", self.on_step_clicked)
            builder.get_object("btn_run").connect("clicked", self.on_run_clicked)
            builder.get_object("btn_reset").connect("clicked", self.on_reset_clicked)

            btn_load = builder.get_object("btn_load")
            if btn_load: btn_load.connect("clicked", self.on_load_clicked)
            btn_save = builder.get_object("btn_save")
            if btn_save: btn_save.connect("clicked", self.on_save_clicked)
        else:
            self._build_fallback_ui()

        self.set_title("Simulador CPU 8-bits - Debugger Visual")
        self.maximize()

        frec_model = Gio.ListStore(item_type=ItemMenu)
        frec_model.append(ItemMenu("1000", "1 s"))
        frec_model.append(ItemMenu("500", "500 ms"))
        frec_model.append(ItemMenu("100", "100 ms"))
        frec_model.append(ItemMenu("10", "10 ms"))
        frec_model.append(ItemMenu("1", "1 ms"))

        expresion = Gtk.PropertyExpression.new(ItemMenu, None, "nombre")
        self.frec_drop.set_expression(expresion)
        self.frec_drop.set_model(frec_model)
        self.frec_drop.set_selected(3)
        self.frec_drop.connect("notify::selected", self.on_frec_changed)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_string("""
            .output {
                font-family: 'Minecraftia', monospace;
                font-size: 10px;
                background: black;
                color: orange;
                padding: 5px;
            }
            .traza {
                background: black;
                color: white;        
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.display_view.add_css_class("output")
        self.trace_view.add_css_class("traza")

        self.io_devices = {
            'in': {0: self.read_keyboard_port},
            'out': {1: self.write_display_port}
        }

        self.memory = Memory(256)
        self.cpu = CPU(self.memory, self.io_devices)
        self.run_timer = None
        self.address_to_line = {}
        self.code_size = 0
        self.data_size = 0

        self.add_font('dogica')
        self.add_font('dogicapixel')
        self.add_font('Minecraftia-Regular')
        self.frec = 10

        mem_buffer = self.mem_view.get_buffer()
        self.tag_mem_highlight = mem_buffer.create_tag("highlight", background="#3584e4", foreground="white", weight=Pango.Weight.BOLD)
        self.tag_code = mem_buffer.create_tag("code_fg", foreground="#4CAF50", weight=Pango.Weight.BOLD)
        self.tag_data = mem_buffer.create_tag("data_fg", foreground="#FF9800", weight=Pango.Weight.BOLD)
        self.tag_stack = mem_buffer.create_tag("stack_fg", foreground="#E91E63", weight=Pango.Weight.BOLD)

        ed_buffer = self.code_view.get_buffer()
        self.tag_ed_highlight = ed_buffer.create_tag("linea_actual", background="#3584e4", foreground="white")

    def _build_fallback_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(main_box)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.set_margin_start(10); toolbar.set_margin_top(10)
        main_box.append(toolbar)

        btn_assemble = Gtk.Button(label="Ensamblar")
        btn_step = Gtk.Button(label="Paso a Paso")
        btn_run = Gtk.Button(label="Ejecutar")
        btn_reset = Gtk.Button(label="Reset")
        btn_load = Gtk.Button(label="Cargar .asm")
        btn_save = Gtk.Button(label="Guardar .asm")

        btn_assemble.connect("clicked", self.on_assemble_clicked)
        btn_step.connect("clicked", self.on_step_clicked)
        btn_run.connect("clicked", self.on_run_clicked)
        btn_reset.connect("clicked", self.on_reset_clicked)
        btn_load.connect("clicked", self.on_load_clicked)
        btn_save.connect("clicked", self.on_save_clicked)

        toolbar.append(btn_assemble)
        toolbar.append(btn_step)
        toolbar.append(btn_run)
        toolbar.append(btn_reset)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        toolbar.append(separator)
        
        toolbar.append(btn_load)
        toolbar.append(btn_save)

        self.frec_drop = Gtk.DropDown()
        toolbar.append(self.frec_drop)

        workspace = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
        workspace.set_margin_start(10); workspace.set_margin_end(10)
        workspace.set_margin_bottom(10); workspace.set_vexpand(True)
        main_box.append(workspace)

        editor_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        lbl_ed = Gtk.Label(label="<b>Editor Assembly</b>", use_markup=True)
        lbl_ed.set_halign(Gtk.Align.START)
        editor_box.append(lbl_ed)
        
        self.code_view = Gtk.TextView()
        self.code_view.set_monospace(True)
        self.code_view.get_buffer().set_text(
            "; --- DEMO: SUBRUTINA DE DIVISIÓN CON SUB/CMP ---\n"
            ".CODE\n"
            "  MOV A, 38         ; Dividendo\n"
            "  MOV B, 5          ; Divisor\n"
            "  CALL dividir\n"
            "  OUT 1, C          ; Cociente esperada: 7\n"
            "  OUT 1, A          ; Resto esperado: 3\n"
            "  HLT\n\n"
            "dividir:\n"
            "  MOV C, 0          ; C = Cociente (Contador)\n"
            "bucle_d:\n"
            "  MOV D, A          ; Copia de A\n"
            "  SUB D, B          ; Probar resta\n"
            "  JC fin_div        ; Si D < B -> termina la división\n\n"
            "  SUB A, B          ; Resta real\n"
            "  ADD C, 1          ; Incrementar cociente\n"
            "  JMP bucle_d\n"
            "fin_div:\n"
            "  RET\n"
        )
        scroll_ed = Gtk.ScrolledWindow()
        scroll_ed.set_child(self.code_view)
        scroll_ed.set_vexpand(True); scroll_ed.set_hexpand(True)
        editor_box.append(scroll_ed)
        workspace.append(editor_box)

        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        center_box.set_hexpand(True)
        workspace.append(center_box)

        lbl_r_title = Gtk.Label(label="<b>Registros</b>", use_markup=True)
        lbl_r_title.set_halign(Gtk.Align.START)
        center_box.append(lbl_r_title)
        self.lbl_regs = Gtk.Label(halign=Gtk.Align.START)
        center_box.append(self.lbl_regs)

        lbl_io_title = Gtk.Label(label="<b>Periféricos I/O</b>", use_markup=True)
        lbl_io_title.set_halign(Gtk.Align.START)
        center_box.append(lbl_io_title)
        
        self.entry_key = Gtk.Entry()
        self.entry_key.set_placeholder_text("Escribe texto aquí...")
        center_box.append(self.entry_key)

        self.display_view = Gtk.TextView(editable=False, monospace=True)
        scroll_disp = Gtk.ScrolledWindow()
        scroll_disp.set_child(self.display_view)
        scroll_disp.set_size_request(-1, 80)
        center_box.append(scroll_disp)

        lbl_tr_title = Gtk.Label(label="<b>Traza de Ejecución</b>", use_markup=True)
        lbl_tr_title.set_halign(Gtk.Align.START)
        center_box.append(lbl_tr_title)

        self.trace_view = Gtk.TextView(editable=False, monospace=True)
        scroll_tr = Gtk.ScrolledWindow()
        scroll_tr.set_child(self.trace_view)
        scroll_tr.set_vexpand(True)
        center_box.append(scroll_tr)

        mem_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        lbl_m_title = Gtk.Label(label="<b>Memoria (Hex)</b>", use_markup=True)
        lbl_m_title.set_halign(Gtk.Align.START)
        mem_box.append(lbl_m_title)

        self.mem_view = Gtk.TextView(editable=False, monospace=True)
        scroll_mem = Gtk.ScrolledWindow()
        scroll_mem.set_child(self.mem_view)
        scroll_mem.set_vexpand(True); scroll_mem.set_hexpand(True)
        mem_box.append(scroll_mem)
        workspace.append(mem_box)

    def on_load_clicked(self, widget):
        dialog = Gtk.FileDialog(title="Cargar archivo Assembly")

        filter_asm = Gtk.FileFilter()
        filter_asm.set_name("Archivos Assembly (*.asm)")
        filter_asm.add_pattern("*.asm")
        
        filters = Gio.ListStore(item_type=Gtk.FileFilter)
        filters.append(filter_asm)
        dialog.set_filters(filters)

        def on_open_finish(dialog, result):
            try:
                file = dialog.open_finish(result)
                if file:
                    path = file.get_path()
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.code_view.get_buffer().set_text(content)
                    self.append_trace(f"Archivo cargado: {os.path.basename(path)}")
            except Exception:
                pass

        dialog.open(self, None, on_open_finish)

    def on_save_clicked(self, widget):
        dialog = Gtk.FileDialog(title="Guardar código Assembly")
        
        filter_asm = Gtk.FileFilter()
        filter_asm.set_name("Archivos Assembly (*.asm)")
        filter_asm.add_pattern("*.asm")
        
        filters = Gio.ListStore(item_type=Gtk.FileFilter)
        filters.append(filter_asm)
        dialog.set_filters(filters)

        def on_save_finish(dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    path = file.get_path()
                    buf = self.code_view.get_buffer()
                    text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    self.append_trace(f"Código guardado en: {os.path.basename(path)}")
            except Exception:
                pass

        dialog.save(self, None, on_save_finish)

    def read_keyboard_port(self):
        text = self.entry_key.get_text()
        if text:
            val = ord(text[0])
            self.entry_key.set_text(text[1:])
            return val
        return 0

    def write_display_port(self, value, is_ascii=True):
        buf = self.display_view.get_buffer()
        if is_ascii:
            char = chr(value) if 32 <= value <= 126 or value == 10 else '?'
            buf.insert(buf.get_end_iter(), char)
        else:
            buf.insert(buf.get_end_iter(), f"{value} ")

    def on_frec_changed(self, dropdown, param):
        item = dropdown.get_selected_item()
        if item:
            self.frec = int(item.item_id)

    def append_trace(self, text):
        buffer = self.trace_view.get_buffer()
        buffer.insert(buffer.get_end_iter(), text + "\n")
        
        def do_scroll():
            mark = buffer.create_mark(None, buffer.get_end_iter(), False)
            self.trace_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
            return False

        GLib.idle_add(do_scroll)

    def on_assemble_clicked(self, widget):
        buf = self.code_view.get_buffer()
        code = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        
        mem_map, addr_line, c_size, d_size, err = Assembler.assemble(code)
        
        if err:
            self.append_trace(f"ERROR: {err}")
            return

        self.memory.reset()
        for addr, val in mem_map.items():
            self.memory.write(addr, val)

        self.cpu.reset()
        self.address_to_line = addr_line
        self.code_size = c_size
        self.data_size = d_size
        
        self.display_view.get_buffer().set_text("")
        self.trace_view.get_buffer().set_text("")
        self.append_trace("--- Program Assembled Successfully ---")
        self.update_ui()

    def on_step_clicked(self, widget):
        if not self.cpu.halted:
            res = self.cpu.step()
            self.append_trace(res)
            self.update_ui()

    def on_run_clicked(self, widget):
        if self.run_timer is not None:
            GLib.source_remove(self.run_timer)
            self.run_timer = None
            widget.set_label("Ejecutar")
            return

        widget.set_label("Pausar")
        
        def run_loop():
            if self.cpu.halted:
                self.run_timer = None
                widget.set_label("Ejecutar")
                return False
            
            res = self.cpu.step()
            self.append_trace(res)
            self.update_ui()
            return True

        self.run_timer = GLib.timeout_add(self.frec, run_loop)

    def on_reset_clicked(self, widget):
        if self.run_timer is not None:
            GLib.source_remove(self.run_timer)
            self.run_timer = None
        self.cpu.reset()
        self.update_ui()

    def update_ui(self):
        current_pc = self.cpu.pc

        regs = self.cpu.registers
        reg_text = (
            f"PC : {current_pc:02X} | SP : {self.cpu.sp:02X}\n"
            f"A  : {regs[0]:02X} | B: {regs[1]:02X} | C: {regs[2]:02X} | D: {regs[3]:02X}\n"
            f"Z-Flag: {'1' if self.cpu.zero_flag else '0'} | C-Flag: {'1' if self.cpu.carry_flag else '0'} | Halt: {'Sí' if self.cpu.halted else 'No'}"
        )
        self.lbl_regs.set_markup(f"<span font_family='monospace'>{reg_text}</span>")

        mem_buffer = self.mem_view.get_buffer()
        mem_lines = []
        for i in range(0, self.memory.size, 8):
            chunk = self.memory.data[i:i+8]
            hex_chunk = " ".join([f"{b:02X}" for b in chunk])
            mem_lines.append(f"{i:02X} | {hex_chunk}")
        
        mem_buffer.set_text("\n".join(mem_lines))

        code_end = self.code_size
        data_end = self.data_size

        for addr in range(self.memory.size):
            line_idx = addr // 8
            char_offset = 5 + (addr % 8) * 3
            _ok1, s_iter = mem_buffer.get_iter_at_line_offset(line_idx, char_offset)
            _ok2, e_iter = mem_buffer.get_iter_at_line_offset(line_idx, char_offset + 2)

            if addr == current_pc:
                mem_buffer.apply_tag(self.tag_mem_highlight, s_iter, e_iter)
            elif 0 <= addr < code_end:
                mem_buffer.apply_tag(self.tag_code, s_iter, e_iter)
            elif code_end <= addr < data_end:
                mem_buffer.apply_tag(self.tag_data, s_iter, e_iter)
            elif addr > self.cpu.sp:
                mem_buffer.apply_tag(self.tag_stack, s_iter, e_iter)

        ed_buffer = self.code_view.get_buffer()
        ed_buffer.remove_tag(self.tag_ed_highlight, ed_buffer.get_start_iter(), ed_buffer.get_end_iter())
        
        if current_pc in self.address_to_line:
            target_line = self.address_to_line[current_pc]
            _ok1, s_line = ed_buffer.get_iter_at_line(target_line)
            e_line = s_line.copy()
            if not e_line.ends_line():
                e_line.forward_to_line_end()
            ed_buffer.apply_tag(self.tag_ed_highlight, s_line, e_line)