from simulator import strong_bisimulation, weak_bisimulation
from simulator import StateGraph
from tkinter import filedialog
from tkinter import ttk
from tkinter import *
import pickle
import time
import os


class UI:
    #################################
    #      Auxiliary functions      #
    #################################
    def nonsense(self):
        self.print_log('Sorry, ' + self.name + ' can not complete this task now.')

    def parse_script_file(self, file_name):
        title_name = file_name[:-4].split('/')[-1]
        file = open(file_name)
        action_string = ''
        target_string = ''
        agent_string = ''
        for line in file:
            if len(line) == 0 or line[0] == '*':
                continue
            elif line.startswith('action'):
                action_string += line.split(' ', 1)[1][:-1]
            elif line.startswith('target'):
                target_string += line.split(' ')[1][:-1]
            elif line.startswith('agent'):
                agent_string += line.split(' ', 1)[1]
            elif line.startswith('quit'):
                break
        self.print_log('Script file ' + title_name + '.txt loaded successfully.')

        return title_name, action_string, target_string, agent_string

    def print_log(self, s):
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + ': ' + s + '\n')
        self.log_text.config(state=DISABLED)

    def clear_log(self):
        self.log_text.config(state=NORMAL)
        self.log_text.delete('1.0', END)
        self.log_text.config(state=DISABLED)

    def save_log(self):
        output_file = open('log/' + time.strftime('%Y%m%d%H%M%S', time.localtime()) + '.log', 'w')
        s = self.log_text.get('1.0', END)
        output_file.write(s)
        output_file.close()

    def freeze_code(self):
        self.title_entry.config(state='readonly')
        self.action_entry.config(state='readonly')
        self.target_entry.config(state='readonly')
        self.agent_text.config(state=DISABLED)

    def graph(self):
        graph_folder_name = self.title_entry.get()
        figure_path = 'graph/' + graph_folder_name + '/'

        figure_count = len(os.listdir(figure_path))
        self.state_graph = PhotoImage(file=figure_path + str(figure_count - 1) + '.png')
        self.canvas.itemconfigure(self.canvas_picture, image=self.state_graph)
        self.canvas.update()

        self.print_log('The whole state graph was shown in canvas. Did it match your own deduction?')

    def bisimulation_ok(self):
        self.bisimulation_agent_1 = self.bisimulation_agent_1_comboxlist.get()
        self.bisimulation_agent_2 = self.bisimulation_agent_2_comboxlist.get()
        self.bisimulation_configuration_window.withdraw()

        pickle_file_1 = open('data/' + self.bisimulation_agent_1 + '.pickle', 'rb')
        state_graph_1 = pickle.load(pickle_file_1)
        pickle_file_1.close()
        pickle_file_2 = open('data/' + self.bisimulation_agent_2 + '.pickle', 'rb')
        state_graph_2 = pickle.load(pickle_file_2)
        pickle_file_2.close()

        self.clear_log()
        info_text = ''
        if self.bisimulation_type.get() == '1':
            info_text += strong_bisimulation(state_graph_1, state_graph_2)
        else:
            info_text += weak_bisimulation(state_graph_1, state_graph_2)

        self.result_text_window = Toplevel()
        self.result_text_window.title('Bisimulation result')
        self.result_text_window.geometry('800x600')

        self.result_text = Text(
            self.result_text_window,
            height=100,
            width=100,
            font=('Arial', 20)
        )
        self.result_text.pack(side=LEFT, fill=BOTH)
        self.result_text.insert(END, info_text)

        self.result_text_window.mainloop()

    def bisimulation_cancel(self):
        self.bisimulation_configuration_window.withdraw()

    def graph_configuration_ok(self):
        self.animation_duration = self.animation_duration_variable.get()
        self.graph_configuration_window.withdraw()

    def graph_configuration_cancel(self):
        self.graph_configuration_window.withdraw()

    #################################
    #   Button response functions   #
    #################################

    def load_script(self):
        file_name = filedialog.askopenfilename(
                initialdir='D:/Lab/PythonProjects/SexyCCS/script',
                title='Select file',
                filetypes=[(' please open txt file', '*.txt')]
        )
        if file_name:
            self.title_entry.config(state=NORMAL)
            self.action_entry.config(state=NORMAL)
            self.target_entry.config(state=NORMAL)
            self.agent_text.config(state=NORMAL)

            self.title_entry.delete(0, END)
            self.action_entry.delete(0, END)
            self.target_entry.delete(0, END)
            self.agent_text.delete(1.0, END)

            title, action, target, agent = self.parse_script_file(file_name)

            self.title_entry.insert(0, title)
            self.action_entry.insert(0, action)
            self.target_entry.insert(0, target)
            self.agent_text.insert(END, agent)

            self.freeze_code()

    def edit(self):
        self.title_entry.config(state=NORMAL)
        self.action_entry.config(state=NORMAL)
        self.target_entry.config(state=NORMAL)
        self.agent_text.config(state=NORMAL)

    def save(self):
        self.freeze_code()

        title = self.title_entry.get()
        action = self.action_entry.get()
        target = self.target_entry.get()
        agent = self.agent_text.get('1.0', END)

        if len(title) == 0:
            return

        output_file = open('script/' + title + '.txt', 'w')

        output_string = '*Define the action name of diagram\n'
        output_string += 'action ' + action + '\n\n'
        output_string += '*Define the knowledge of diagram\n'
        for agent_string in agent.split('\n'):
            if len(agent_string) == 0:
                continue
            output_string += 'agent ' + agent_string + '\n'
        output_string += '\n*Define the target agent to be simulated\n'
        output_string += 'target ' + target + '\n\n'
        output_string += '*End of command list' + '\nquit'

        output_file.write(output_string)
        output_file.close()
        self.print_log('The script file ' + title + '.txt has been saved.')

    def simulate(self):
        self.freeze_code()

        title = self.title_entry.get()
        action = self.action_entry.get()
        target = self.target_entry.get()
        agent = self.agent_text.get('1.0', END)

        graph_name = title
        action_words = action.split(' ')
        target_state_string = target
        agent_string_lines = agent.split('\n')
        state_map = {}
        for agent_string in agent_string_lines:
            if len(agent_string):
                agent_define_pair = agent_string.split('=')
                agent_name = re.sub(' ', '', agent_define_pair[0])
                agent_definition = re.sub(' ', '', agent_define_pair[1])
                state_map[agent_name] = agent_definition

        start_time = time.time()
        new_state_graph = StateGraph(graph_name, action_words, target_state_string, state_map)
        end_time = time.time()

        self.print_log('Simulation completed successfully. Elapsed time - ' + '%.3f' % (end_time - start_time) + 's')

        output_file = open('data/' + title + '.pickle', 'wb')
        pickle.dump(new_state_graph, output_file)
        output_file.close()

        for row in self.table.get_children():
            self.table.delete(row)
        state_num = 0
        for state in new_state_graph.state_name_list:
            self.table.insert('', state_num, values=(state_num, state))
            state_num += 1

        self.graph()

    def show_text_result(self):
        self.freeze_code()
        title = self.title_entry.get()

        pickle_file = open('data/' + title + '.pickle', 'rb')
        current_state_graph = pickle.load(pickle_file)
        pickle_file.close()

        info_text = 'Totally, there are ' + str(current_state_graph.state_size) + ' states:\n\n'
        for i in range(current_state_graph.state_size):
            info_text += str(i) + ': ' + current_state_graph.state_name_list[i] + '\n'

        info_text += '\nThe transfer functions(adjacent state map) are:\n'
        for state_num in range(current_state_graph.state_size):
            state = current_state_graph.state_name_list[state_num]
            info_text += '\n' + state + ':\n'
            for action in current_state_graph.numeric_adjacent_map_list[state_num]:
                for next_state_num in current_state_graph.numeric_adjacent_map_list[state_num][action]:
                    next_state = current_state_graph.state_name_list[next_state_num]
                    if action == r'$ \tau $':
                        info_text += '     ---tau-->     ' + next_state + '\n'
                    else:
                        info_text += '     ---' + action + '-->     ' + next_state + '\n'

        self.result_text_window = Toplevel()
        self.result_text_window.title('Simulation result of ' + current_state_graph.name)
        self.result_text_window.geometry('800x600')

        self.result_text = Text(
            self.result_text_window,
            height=100,
            width=100,
            font=('Arial', 20)
        )
        self.result_text.pack(side=LEFT, fill=BOTH)
        self.result_text.insert(END, info_text)

        self.result_text_window.mainloop()

    def animation(self):
        self.freeze_code()
        graph_folder_name = self.title_entry.get()
        figure_path = 'graph/' + graph_folder_name + '/'

        figure_count = len(os.listdir(figure_path))
        for graph_id in range(figure_count):
            self.state_graph = PhotoImage(file=figure_path + str(graph_id) + '.png')
            self.canvas.itemconfigure(self.canvas_picture, image=self.state_graph)
            self.canvas.update()
            time.sleep(self.animation_duration)

        self.print_log('The animation was so cool, right? For more details, you can click the text result button.')

    def bisimulation(self):
        self.bisimulation_configuration_window = Toplevel()
        self.bisimulation_configuration_window.title('Bisimulation configuration')
        self.bisimulation_configuration_window.geometry('400x300')
        self.bisimulation_configuration_window.resizable(height=False, width=False)

        Label(
            self.bisimulation_configuration_window,
            text='Please choose a bisimulation type:',
            height=1,
            width=40,
            anchor='nw',
            font=('Arial', 12)
        ).place(x=10, y=10)

        self.bisimulation_type.set('1')

        Radiobutton(
            self.bisimulation_configuration_window,
            variable=self.bisimulation_type,
            value='1',
            text='strong bisimulation',
            font=('Arial', 12)
        ).place(x=115, y=40)

        Radiobutton(
            self.bisimulation_configuration_window,
            variable=self.bisimulation_type,
            value='2',
            text='weak bisimulation',
            font=('Arial', 12)
        ).place(x=115, y=70)

        Label(
            self.bisimulation_configuration_window,
            text='Please choose a bisimulation pair:',
            height=1,
            width=40,
            anchor='nw',
            font=('Arial', 12)
        ).place(x=10, y=110)

        Label(
            self.bisimulation_configuration_window,
            text='Agent 1:',
            height=1,
            width=7,
            anchor='center',
            font=('Arial', 12)
        ).place(x=60, y=150)

        Label(
            self.bisimulation_configuration_window,
            text='Agent 2:',
            height=1,
            width=7,
            anchor='center',
            font=('Arial', 12)
        ).place(x=60, y=180)

        pickle_file_name_list = os.listdir('data')
        agent_name_list = []
        for pickle_file_name in pickle_file_name_list:
            if pickle_file_name.endswith('.pickle'):
                agent_name_list.append(pickle_file_name[:-7])

        self.bisimulation_agent_1_comboxlist = ttk.Combobox(
            self.bisimulation_configuration_window,
            textvariable=self.bisimulation_agent_1,
            font=('Arial', 12),
            justify='center'
        )

        self.bisimulation_agent_1_comboxlist['values'] = tuple(agent_name_list)
        self.bisimulation_agent_1_comboxlist.current(0)
        self.bisimulation_agent_1_comboxlist.place(x=135, y=150)

        self.bisimulation_agent_2_comboxlist = ttk.Combobox(
            self.bisimulation_configuration_window,
            textvariable=self.bisimulation_agent_2,
            font=('Arial', 12),
            justify='center'
        )

        self.bisimulation_agent_2_comboxlist['values'] = tuple(agent_name_list)
        self.bisimulation_agent_2_comboxlist.current(0)
        self.bisimulation_agent_2_comboxlist.place(x=135, y=180)

        Button(
            self.bisimulation_configuration_window,
            text='OK',
            height=1,
            width=8,
            font=('Arial', 12),
            bd=5,
            command=self.bisimulation_ok
        ).place(x=100, y=230)

        Button(
            self.bisimulation_configuration_window,
            text='Cancel',
            height=1,
            width=8,
            font=('Arial', 12),
            bd=5,
            command=self.bisimulation_cancel
        ).place(x=220, y=230)

        self.bisimulation_configuration_window.mainloop()

    def graph_configuration(self):
        self.graph_configuration_window = Toplevel()
        self.graph_configuration_window.title('Graph configuration')
        self.graph_configuration_window.geometry('300x200')
        self.graph_configuration_window.resizable(height=False, width=False)

        Label(
            self.graph_configuration_window,
            text='Please set the pause time of animation:',
            height=1,
            width=30,
            anchor='nw',
            font=('Arial', 10)
        ).place(x=10, y=10)

        Scale(
            self.graph_configuration_window,
            from_=0.2,
            to=2.0,
            tickinterval=0.3,
            resolution=0.01,
            variable=self.animation_duration_variable,
            orient=HORIZONTAL,
            length=200,
            showvalue=1
        ).place(x=50, y=40)

        Button(
            self.graph_configuration_window,
            text='OK',
            height=1,
            width=6,
            font=('Arial', 10),
            bd=5,
            command=self.graph_configuration_ok
        ).place(x=70, y=120)

        Button(
            self.graph_configuration_window,
            text='Cancel',
            height=1,
            width=6,
            font=('Arial', 10),
            bd=5,
            command=self.graph_configuration_cancel
        ).place(x=170, y=120)

        self.graph_configuration_window.mainloop()

    #################################
    #         Initialize UI         #
    #################################
    def __init__(self, name):
        self.name = name
        self.root = Tk()

        # Init root window
        self.root.title('SexyCCS')
        self.root.geometry('1920x1080')
        self.root.resizable(height=True, width=True)

        # Init menu bar with file_menu, setting_menu, tool_menu and help menu
        self.menubar = Menu(self.root)
        self.root.config(menu=self.menubar)

        self.file_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='File', menu=self.file_menu)
        self.file_menu.add_command(label='Load Script', command=self.load_script)
        self.file_menu.add_command(label='Save Script', command=self.save)
        self.file_menu.add_command(label='Clear Log', command=self.clear_log)
        self.file_menu.add_command(label='Save Log', command=self.save_log)
        self.file_menu.add_separator()
        self.file_menu.add_command(label='Exit', command=self.root.withdraw)

        self.setting_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Settings', menu=self.setting_menu)
        self.setting_menu.add_command(label='Graph Type', command=self.nonsense)
        self.setting_menu.add_command(label='Animation Pause', command=self.nonsense)
        self.setting_menu.add_command(label='Background Figure', command=self.nonsense)

        self.tool_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Tools', menu=self.tool_menu)
        self.tool_menu.add_command(label='Simulate', command=self.simulate)
        self.tool_menu.add_command(label='Bisimulation', command=self.bisimulation)

        self.help_menu = Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label='Help', menu=self.help_menu)
        self.help_menu.add_command(label='Code Example', command=self.nonsense)
        self.help_menu.add_command(label='Operation Guide', command=self.nonsense)
        self.help_menu.add_command(label='CCS Semantics', command=self.nonsense)
        self.help_menu.add_command(label='More Information', command=self.nonsense)

        #################################
        #     Allocate frame blocks     #
        #################################

        # Node table with vertical scrollbar
        self.node_table_frame = Frame(self.root)
        self.node_table_frame.config(height=800, width=390, padx=5)
        self.node_table_frame.place(x=0, y=5)

        self.table = ttk.Treeview(self.node_table_frame, height=38, show='headings')
        self.table['columns'] = ('node', 'state')
        self.table.column('node', width=60, anchor='center', stretch=False)
        self.table.column('state', width=300, anchor='w', stretch=False)
        self.table.heading('node', text='node')
        self.table.heading('state', text='state')

        self.style = ttk.Style()
        self.style.configure('Treeview.Heading', font=('Arial', 16))
        self.style.configure('Treeview', rowheight=20, font=('Arial', 14))
        self.vsb = Scrollbar(self.node_table_frame, orient='vertical', command=self.table.yview)
        self.hsb = Scrollbar(self.node_table_frame, orient='horizontal', command=self.table.xview)
        self.vsb.pack(side='right', fill='y')
        self.hsb.pack(side='bottom', fill='x')
        self.table.configure(yscrollcommand=self.vsb.set)
        self.table.configure(xscrollcommand=self.hsb.set)
        self.table.pack(side=LEFT, fill=BOTH)

        # Canvas zone to demo state graph
        self.state_graph_frame = Frame(self.root)
        self.state_graph_frame.config(height=803, width=800, padx=5)
        self.state_graph_frame.place(x=400, y=3)

        self.canvas = Canvas(self.state_graph_frame, height=803, width=800, bg='white')
        self.canvas.pack(fill=BOTH, expand=True)
        self.picture = PhotoImage(file='icon/background.png')
        self.canvas_picture = self.canvas.create_image(400, 400, image=self.picture)

        # Code frame with containers of title, action, target and agent
        self.code_frame = Frame(self.root)
        self.code_frame.config(height=800, width=600, padx=10)
        self.code_frame.place(x=1215, y=5)

        self.code_title_label = Label(self.root, height=2, width=6, text='title:', font=('Arial', 12))
        self.code_title_label.place(x=1215, y=0)

        self.code_title_frame = Frame(self.root)
        self.code_title_frame.config(height=50, width=560)
        self.code_title_frame.place(x=1280, y=5)

        self.title_entry = Entry(self.code_title_frame)
        self.title_entry.config(width=33, font=('Arial', 22), state='readonly')
        self.title_entry.pack(fill=BOTH)

        self.code_action_frame = Frame(self.root)
        self.code_action_frame.config(height=50, width=560)
        self.code_action_frame.place(x=1280, y=60)

        self.code_action_label = Label(self.root, height=2, width=6, text='action:', font=('Arial', 12))
        self.code_action_label.place(x=1215, y=55)

        self.action_entry = Entry(self.code_action_frame)
        self.action_entry.config(width=33, font=('Arial', 22), state='readonly')
        self.action_entry.pack(fill=BOTH)

        self.code_target_frame = Frame(self.root)
        self.code_target_frame.config(height=50, width=560)
        self.code_target_frame.place(x=1280, y=115)

        self.code_target_label = Label(self.root, height=2, width=6, text='target:', font=('Arial', 12))
        self.code_target_label.place(x=1215, y=110)

        self.target_entry = Entry(self.code_target_frame)
        self.target_entry.config(width=33, font=('Arial', 22), state='readonly')
        self.target_entry.pack(fill=BOTH)

        self.code_agent_frame = Frame(self.root)
        self.code_agent_frame.config(bg='green', height=638, width=600)
        self.code_agent_frame.place(x=1215, y=170)

        self.agent_text = Text(self.code_agent_frame)
        self.agent_text.config(height=14, width=27, font=('Arial', 30), state=DISABLED)
        self.agent_text.pack(fill=BOTH)

        # Operation frame with edit, save, simulate, text, graph and animation buttons
        self.operation_frame = Frame(self.root)
        self.operation_frame.config(height=800, width=85, padx=10, pady=5)
        self.operation_frame.place(x=1820, y=5)

        self.operation_edit_frame = Frame(self.root)
        self.operation_edit_frame.config(height=85, width=85, pady=5)
        self.operation_edit_frame.place(x=1820, y=5)

        self.edit_icon = PhotoImage(file='icon/edit.png').subsample(12, 12)
        self.edit_button = Button(self.operation_edit_frame, image=self.edit_icon, height=78, width=78, command=self.edit)
        self.edit_button.pack(fill=BOTH)

        self.operation_save_frame = Frame(self.root)
        self.operation_save_frame.config(height=85, width=85, pady=5)
        self.operation_save_frame.place(x=1820, y=95)

        self.save_icon = PhotoImage(file='icon/save.png').subsample(5, 5)
        self.save_button = Button(self.operation_save_frame, image=self.save_icon, height=78, width=78, command=self.save)
        self.save_button.pack(fill=BOTH)

        self.operation_simulate_frame = Frame(self.root)
        self.operation_simulate_frame.config(height=85, width=85, pady=5)
        self.operation_simulate_frame.place(x=1820, y=185)

        self.simulate_icon = PhotoImage(file='icon/simulate.png').subsample(5, 5)
        self.simulate_button = Button(self.operation_simulate_frame, image=self.simulate_icon, height=78, width=78, command=self.simulate)
        self.simulate_button.pack(fill=BOTH)

        self.operation_text_frame = Frame(self.root)
        self.operation_text_frame.config(height=85, width=85, pady=5)
        self.operation_text_frame.place(x=1820, y=275)

        self.text_icon = PhotoImage(file='icon/text.png').subsample(8, 8)
        self.text_button = Button(self.operation_text_frame, image=self.text_icon, height=78, width=78, command=self.show_text_result)
        self.text_button.pack(fill=BOTH)

        self.operation_bisimulation_frame = Frame(self.root)
        self.operation_bisimulation_frame.config(height=85, width=85, pady=5)
        self.operation_bisimulation_frame.place(x=1820, y=365)

        self.bisimulation_icon = PhotoImage(file='icon/bisimulation.png').subsample(8, 8)
        self.bisimulation_button = Button(self.operation_bisimulation_frame, image=self.bisimulation_icon, height=78, width=78, command=self.bisimulation)
        self.bisimulation_button.pack(fill=BOTH)

        self.operation_animation_frame = Frame(self.root)
        self.operation_animation_frame.config(height=85, width=85, pady=5)
        self.operation_animation_frame.place(x=1820, y=455)

        self.animation_icon = PhotoImage(file='icon/animation.png').subsample(5, 5)
        self.animation_button = Button(self.operation_animation_frame, image=self.animation_icon, height=78, width=78, command=self.animation)
        self.animation_button.pack(fill=BOTH)

        self.operation_graph_configuration_frame = Frame(self.root)
        self.operation_graph_configuration_frame.config(height=85, width=85, pady=5)
        self.operation_graph_configuration_frame.place(x=1820, y=545)

        self.graph_configuration_icon = PhotoImage(file='icon/graph.png').subsample(7, 7)
        self.graph_configuration_button = Button(self.operation_graph_configuration_frame, image=self.graph_configuration_icon, height=78, width=78, command=self.graph_configuration)
        self.graph_configuration_button.pack(fill=BOTH)

        # Log frame with scrollbar to print log information
        self.log_frame = Frame(self.root)
        self.log_frame.config(height=210, width=1900)
        self.log_frame.place(x=5, y=810)

        self.log_text = Text(self.log_frame)
        self.log_text.config(height=9, width=171, font=('Arial', 14))
        self.log_text.pack(side='left', fill=BOTH)

        self.vsb_1 = Scrollbar(self.log_frame)
        self.vsb_1.config(orient='vertical', command=self.log_text.yview)
        self.vsb_1.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=self.vsb_1.set)

        self.print_log('Hi, I\'m your CCS assistant ' + self.name + '. My pleasure to work for you.')
        self.log_text.config(state=DISABLED)

        self.state_graph = None

        self.result_text_window = None
        self.result_text = None

        self.graph_configuration_window = None
        self.animation_duration_variable = DoubleVar()
        self.animation_duration = 0.5

        self.bisimulation_configuration_window = None
        self.bisimulation_type = StringVar()
        self.bisimulation_agent_1_comboxlist = None
        self.bisimulation_agent_1 = StringVar()
        self.bisimulation_agent_2_comboxlist = None
        self.bisimulation_agent_2 = StringVar()

    #################################
    #              Run              #
    #################################
    def run(self):
        self.root.mainloop()


if __name__ == '__main__':
    ui = UI('Qian Qian')
    ui.run()
