import tkinter as tk
from tkinter import messagebox
import random

class NumberEliminationGame:
    def __init__(self, root):
        self.root = root
        self.root.title("数字10消除游戏")
        self.root.resizable(False, False)
        
        # 游戏常量设置
        self.ROWS = 10
        self.COLS = 16
        self.CELL_SIZE = 40
        self.BOARD_PADDING = 20  # 棋盘周围的填充
        self.GAME_TIME = 120  # 游戏时间120秒
        
        # 颜色定义
        self.COLORS = {
            'bg': 'white',
            'cell': 'lightgray',
            'selected': 'lightblue',
            'text': 'black',
            'highlight': 'green',
            'hint': 'red'  # 提示颜色
        }
        
        # 初始化游戏状态
        self.board = [[random.randint(1, 9) for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.selected_cells = []
        self.hint_rect = None  # 用于存储提示的矩形框坐标
        self.message = tk.StringVar()
        self.message.set("")
        self.game_over = False  # 游戏结束标志
        self.score = 0  # 初始化分数
        self.time_left = self.GAME_TIME  # 剩余时间
        self.timer_id = None  # 计时器ID
        
        # 框选相关变量
        self.drawing_selection = False
        self.selection_start = None
        self.selection_end = None
        self.selection_rect = None
        
        # 创建界面
        self.create_widgets()
        self.update_display()
        self.start_timer()  # 开始计时
    
    def create_widgets(self):
        # 主框架
        main_frame = tk.Frame(self.root, bg=self.COLORS['bg'])
        main_frame.pack(padx=10, pady=10)
        
        # 游戏区域
        canvas_width = self.COLS*self.CELL_SIZE + 2*self.BOARD_PADDING
        canvas_height = self.ROWS*self.CELL_SIZE + 2*self.BOARD_PADDING
        self.canvas = tk.Canvas(main_frame, width=canvas_width, height=canvas_height, bg=self.COLORS['bg'])
        self.canvas.pack()
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        # 信息显示区域
        info_frame = tk.Frame(main_frame, bg=self.COLORS['bg'])
        info_frame.pack(pady=10, fill='x')
        
        self.sum_label = tk.Label(info_frame, text="当前选择和: 0", font=("Arial", 12), bg=self.COLORS['bg'])
        self.sum_label.pack(side='left')
        
        self.score_label = tk.Label(info_frame, text=f"得分: {self.score}", font=("Arial", 12), bg=self.COLORS['bg'])
        self.score_label.pack(side='left', padx=(20, 0))
        
        self.time_label = tk.Label(info_frame, text=f"剩余时间: {self.time_left}s", font=("Arial", 12), bg=self.COLORS['bg'])
        self.time_label.pack(side='left', padx=(20, 0))
        
        self.hint_label = tk.Label(info_frame, text="", font=("Arial", 12), fg=self.COLORS['highlight'], bg=self.COLORS['bg'])
        self.hint_label.pack(side='left', padx=(20, 0))
        
        message_label = tk.Label(main_frame, textvariable=self.message, font=("Arial", 12), fg='red', bg=self.COLORS['bg'])
        message_label.pack()
        
        # 控制按钮
        button_frame = tk.Frame(main_frame, bg=self.COLORS['bg'])
        button_frame.pack(pady=10)
        
        reset_btn = tk.Button(button_frame, text="重新开始 (R)", command=self.reset_game)
        reset_btn.pack(side='left', padx=5)
        
        hint_btn = tk.Button(button_frame, text="提示 (H)", command=self.show_hint)  # 提示按钮
        hint_btn.pack(side='left', padx=5)
        
        # 绑定键盘事件
        self.root.bind('<Key-r>', lambda e: self.reset_game())
        self.root.bind('<Key-h>', lambda e: self.show_hint())  # 绑定H键触发提示
        self.root.focus_set()
    
    def draw_board(self):
        self.canvas.delete("all")
        
        # 绘制背景
        canvas_width = self.COLS*self.CELL_SIZE + 2*self.BOARD_PADDING
        canvas_height = self.ROWS*self.CELL_SIZE + 2*self.BOARD_PADDING
        self.canvas.create_rectangle(0, 0, canvas_width, canvas_height, fill=self.COLORS['bg'], outline='')
        
        for row in range(self.ROWS):
            for col in range(self.COLS):
                # 添加偏移量以考虑填充
                x1 = self.BOARD_PADDING + col * self.CELL_SIZE
                y1 = self.BOARD_PADDING + row * self.CELL_SIZE
                x2 = x1 + self.CELL_SIZE
                y2 = y1 + self.CELL_SIZE
                
                # 绘制单元格背景（总是灰色）
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=self.COLORS['cell'], outline='black')
                
                # 绘制数字
                number = self.board[row][col]
                if number > 0:  # 只绘制未消除的数字
                    self.canvas.create_text(
                        (x1+x2)//2, 
                        (y1+y2)//2, 
                        text=str(number), 
                        fill=self.COLORS['text'],
                        font=("Arial", 16)
                    )
        
        # 绘制选择框
        if self.selection_rect:
            self.canvas.create_rectangle(
                self.selection_rect[0],
                self.selection_rect[1],
                self.selection_rect[2],
                self.selection_rect[3],
                outline='blue',
                width=2,
                dash=(4, 2)
            )
        
        # 绘制提示框
        if self.hint_rect:
            self.canvas.create_rectangle(
                self.hint_rect[0],
                self.hint_rect[1],
                self.hint_rect[2],
                self.hint_rect[3],
                outline=self.COLORS['hint'],
                width=3
            )
    
    def get_cell_position(self, x, y):
        """根据鼠标位置获取对应的单元格行列"""
        # 考虑填充偏移量
        col = (x - self.BOARD_PADDING) // self.CELL_SIZE
        row = (y - self.BOARD_PADDING) // self.CELL_SIZE
        
        # 检查是否在有效范围内
        if 0 <= row < self.ROWS and 0 <= col < self.COLS:
            # 确保点击位置在实际单元格内
            if (self.BOARD_PADDING <= x < self.BOARD_PADDING + self.COLS * self.CELL_SIZE and 
                self.BOARD_PADDING <= y < self.BOARD_PADDING + self.ROWS * self.CELL_SIZE):
                return row, col
        return None, None
    
    def toggle_selection(self, row, col):
        """切换单元格的选中状态"""
        if self.board[row][col] > 0:  # 只能选择未消除的数字
            if (row, col) in self.selected_cells:
                self.selected_cells.remove((row, col))
            else:
                self.selected_cells.append((row, col))
    
    def clear_selected_if_sum_is_ten(self):
        """如果选中数字之和为10，则清除这些数字"""
        if not self.selected_cells or self.game_over:
            return False
            
        sum_value = sum(self.board[r][c] for r, c in self.selected_cells)
        if sum_value == 10:
            for r, c in self.selected_cells:
                self.board[r][c] = 0  # 0表示已消除
            self.selected_cells.clear()
            
            # 增加分数
            self.score += 100
            self.score_label.config(text=f"得分: {self.score}")
            
            # 检查游戏是否结束（只有在玩家主动消除时才检查）
            if self.check_game_over():
                self.game_over = True
                self.message.set("游戏结束！没有可消除的数字组合了。")
                self.stop_timer()
            
            # 只在玩家主动操作成功时显示消息
            if not self.game_over:
                self.message.set("成功消除!")
                self.root.after(2000, lambda: self.message.set(""))  # 2秒后清除消息
                
            self.update_display()  # 添加这一行确保界面更新
            return True
        else:
            self.message.set(f"和为 {sum_value}，需要等于10")
            self.root.after(2000, lambda: self.message.set(""))  # 2秒后清除消息
            return False
    
    def start_timer(self):
        """开始计时器"""
        self.update_timer()
    
    def update_timer(self):
        """更新计时器"""
        if self.time_left > 0 and not self.game_over:
            self.time_left -= 1
            self.time_label.config(text=f"剩余时间: {self.time_left}s")
            
            # 当时间少于10秒时，用红色显示
            if self.time_left <= 10:
                self.time_label.config(fg='red')
            
            # 安排下一次更新
            self.timer_id = self.root.after(1000, self.update_timer)
        elif self.time_left <= 0 and not self.game_over:
            # 时间到，游戏结束
            self.game_over = True
            self.message.set("时间到！游戏结束！")
            self.stop_timer()
            self.update_display()
    
    def stop_timer(self):
        """停止计时器"""
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None
    
    def show_hint(self):
        """显示提示：找出和为10的一组数字并用红框标记"""
        if self.game_over:
            return
            
        # 清除之前的提示
        self.hint_rect = None
        
        # 查找和为10的矩形框
        hint_result = self.find_rectangular_hint()
        
        if hint_result:
            self.hint_rect = hint_result['rect']
            self.message.set("提示已显示！")
        else:
            self.message.set("未找到合适的提示")
            
        self.root.after(2000, lambda: self.message.set(""))
        self.update_display()
    
    def find_rectangular_hint(self):
        """查找可以形成矩形框且和为10的数字组合"""
        # 获取所有未消除的数字及其位置
        cells_with_positions = []
        for row in range(self.ROWS):
            for col in range(self.COLS):
                if self.board[row][col] > 0:
                    cells_with_positions.append((row, col))
        
        # 尝试不同的矩形区域
        for row1 in range(self.ROWS):
            for col1 in range(self.COLS):
                # 起始点必须是有效数字
                if self.board[row1][col1] <= 0:
                    continue
                    
                for row2 in range(row1, self.ROWS):
                    for col2 in range(col1, self.COLS):
                        # 收集这个矩形区域内的所有数字
                        numbers_in_rect = []
                        positions_in_rect = []
                        
                        for r in range(row1, row2 + 1):
                            for c in range(col1, col2 + 1):
                                if self.board[r][c] > 0:
                                    numbers_in_rect.append(self.board[r][c])
                                    positions_in_rect.append((r, c))
                        
                        # 检查是否有数字在这个矩形区域内
                        if len(numbers_in_rect) > 0 and sum(numbers_in_rect) == 10:
                            # 符合条件，返回矩形框坐标（加上填充偏移量）
                            x1 = self.BOARD_PADDING + col1 * self.CELL_SIZE
                            y1 = self.BOARD_PADDING + row1 * self.CELL_SIZE
                            x2 = self.BOARD_PADDING + (col2 + 1) * self.CELL_SIZE
                            y2 = self.BOARD_PADDING + (row2 + 1) * self.CELL_SIZE
                            
                            return {
                                'rect': (x1, y1, x2, y2),
                                'numbers': numbers_in_rect,
                                'positions': positions_in_rect
                            }
        
        return None  # 没有找到合适的矩形框
    
    def check_game_over(self):
        """检查游戏是否结束（没有和为10的组合）"""
        # 复用提示查找逻辑，如果没有找到任何提示，则游戏结束
        return self.find_rectangular_hint() is None
    
    def update_display(self):
        """更新显示"""
        self.draw_board()
        
        # 更新选中数字之和
        if self.selected_cells:
            sum_value = sum(self.board[r][c] for r, c in self.selected_cells)
            self.sum_label.config(text=f"当前选择和: {sum_value}")
            
            # 如果和为10，提示可以消除
            if sum_value == 10:
                self.hint_label.config(text="点击任意选中数字以消除")
            else:
                self.hint_label.config(text="")
        else:
            self.sum_label.config(text="当前选择和: 0")
            self.hint_label.config(text="")
    
    def on_click(self, event):
        """处理点击事件"""
        if self.game_over:
            return
            
        # 开始绘制选择框
        self.drawing_selection = True
        self.selection_start = (event.x, event.y)
        self.selection_end = (event.x, event.y)
        self.selected_cells.clear()
        self.hint_rect = None  # 清除提示
        
        # 删除之前的选择框
        if self.selection_rect:
            self.selection_rect = None
            
        self.update_display()

    def on_drag(self, event):
        """处理拖拽事件"""
        if self.game_over or not (self.drawing_selection and self.selection_start):
            return
            
        # 更新选择框的结束点
        self.selection_end = (event.x, event.y)
        
        # 计算选择框坐标
        x1, y1 = self.selection_start
        x2, y2 = self.selection_end
        
        # 确保坐标正确（处理从右下到左上的情况）
        left = min(x1, x2)
        top = min(y1, y2)
        right = max(x1, x2)
        bottom = max(y1, y2)
        
        self.selection_rect = (left, top, right, bottom)
        
        # 计算在选择框内的单元格
        self.selected_cells.clear()
        for row in range(self.ROWS):
            for col in range(self.COLS):
                # 添加偏移量以考虑填充
                cell_x1 = self.BOARD_PADDING + col * self.CELL_SIZE
                cell_y1 = self.BOARD_PADDING + row * self.CELL_SIZE
                cell_x2 = cell_x1 + self.CELL_SIZE
                cell_y2 = cell_y1 + self.CELL_SIZE
                
                # 检查单元格是否与选择框有交集
                if (cell_x1 < right and cell_x2 > left and 
                    cell_y1 < bottom and cell_y2 > top and
                    self.board[row][col] > 0):
                    self.selected_cells.append((row, col))
        
        self.update_display()

    def on_release(self, event):
        """处理鼠标释放事件"""
        if self.game_over:
            return
            
        if self.drawing_selection:
            self.drawing_selection = False
            # 鼠标释放后清除选择框
            self.selection_rect = None
            
            # 检查当前选中的数字之和是否为10
            if self.selected_cells:
                sum_value = sum(self.board[r][c] for r, c in self.selected_cells)
                if sum_value == 10:
                    self.clear_selected_if_sum_is_ten()
            
            self.update_display()
    
    def reset_game(self):
        """重新开始游戏"""
        # 停止当前计时器
        self.stop_timer()
        
        self.board = [[random.randint(1, 9) for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.selected_cells.clear()
        self.hint_rect = None  # 清除提示
        self.message.set("")
        self.game_over = False  # 重置游戏结束标志
        self.score = 0  # 重置分数
        self.score_label.config(text=f"得分: {self.score}")
        self.time_left = self.GAME_TIME  # 重置时间
        self.time_label.config(text=f"剩余时间: {self.time_left}s", fg='black')  # 重置时间显示颜色
        self.update_display()
        self.start_timer()  # 重新开始计时

def main():
    root = tk.Tk()
    game = NumberEliminationGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()