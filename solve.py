import math
import re
import tkinter as tk
from tkinter import messagebox
import json
import os

# 定义数据文件路径
DATA_FILE = "data.json"

def parse_angle(angle_str):
    """
    解析以“度°分′”形式输入的角度字符串，并转换为度和分的浮点数。
    例如，输入 "30°15.5′" 将被解析为30度15.5分。
    """
    # 支持带小数的弧分
    match = re.match(r'^\s*(\d+)°\s*([\d.]+)′\s*$', angle_str)
    if match:
        degrees = float(match.group(1))
        minutes = float(match.group(2))
        return degrees, minutes
    else:
        raise ValueError("输入格式错误。请使用 '度°分′' 形式，例如 '30°15.5′'。")

def degrees_minutes_to_decimal(degrees, minutes):
    """将度和分转换为十进制度数。"""
    return degrees + minutes / 60

def decimal_to_degrees_minutes(decimal_degrees):
    """将十进制度数转换为度和分。"""
    degrees = int(decimal_degrees)
    minutes = (decimal_degrees - degrees) * 60
    return degrees, minutes

def calculate_results(angle_inputs):
    """
    根据五组角度输入，计算 Φ̄, S_Φ, Δ_Φ, d, Δ_d, E_d 及最终结果 d = d̄ ± Δ_d。
    """
    n = 5  # 输入组数
    lambda_nm = 546.1  # 波长，单位纳米
    delta_instrument_arcmin = 1  # 仪器不确定度，单位弧分

    angles_deg_min = []
    angles_decimal = []

    # 解析输入并转换为十进制度数
    for angle_str in angle_inputs:
        degrees, minutes = parse_angle(angle_str)
        angles_deg_min.append((degrees, minutes))
        decimal = degrees_minutes_to_decimal(degrees, minutes)
        angles_decimal.append(decimal)

    # 计算平均角度 Φ̄
    phi_bar_decimal = sum(angles_decimal) / n

    # 计算角度的标准差 S_Φ
    variance = sum((phi - phi_bar_decimal) ** 2 for phi in angles_decimal) / (n - 1)
    s_phi_decimal = math.sqrt(variance)

    # 计算仪器不确定度 Δ仪，转换为度
    delta_instrument = delta_instrument_arcmin / 60  # 转换为度

    # 计算总不确定度 Δ_Φ
    delta_phi = math.sqrt(s_phi_decimal ** 2 + delta_instrument ** 2)

    # 将 Δ_Φ 转换为弧度
    delta_phi_rad = math.radians(delta_phi)

    # 计算平均距离 \overline{d} = λ / sin(Φ̄)
    phi_bar_rad = math.radians(phi_bar_decimal)
    sin_phi_bar = math.sin(phi_bar_rad)
    if sin_phi_bar == 0:
        raise ZeroDivisionError("平均角度的正弦值为零，无法计算距离。")
    d_bar_nm = lambda_nm / sin_phi_bar
    d_bar_mm = d_bar_nm / 1e6  # 转换为毫米

    # 计算 Δ_d = (λ cos Φ̄) / sin² Φ̄ * Δ_Φ
    cos_phi_bar = math.cos(phi_bar_rad)
    delta_d_nm = (lambda_nm * cos_phi_bar) / (sin_phi_bar ** 2) * delta_phi_rad
    delta_d_mm = delta_d_nm / 1e6  # 转换为毫米

    # 计算相对不确定度 E_d = (Δ_d / \overline{d}) * 100%
    E_d = (delta_d_mm / d_bar_mm) * 100

    # 计算最终结果 d = \overline{d} ± Δ_d
    d_min_mm = d_bar_mm - delta_d_mm
    d_max_mm = d_bar_mm + delta_d_mm

    # 将 Φ̄ 和 S_Φ 转换回度和分
    phi_bar_deg, phi_bar_min = decimal_to_degrees_minutes(phi_bar_decimal)
    s_phi_deg, s_phi_min = decimal_to_degrees_minutes(s_phi_decimal)
    # 不再需要将 Δ_Φ 转换为度和分，因为它将以弧度形式输出

    # 构造结果字典
    results = {
        "Phi_bar_deg": phi_bar_deg,
        "Phi_bar_min": phi_bar_min,
        "S_phi_deg": s_phi_deg,
        "S_phi_min": s_phi_min,
        "Delta_phi_rad": delta_phi_rad,
        "d_bar_mm": d_bar_mm,
        "Delta_d_mm": delta_d_mm,
        "E_d_percent": E_d,
        "d_min_mm": d_min_mm,
        "d_max_mm": d_max_mm
    }

    return results

def save_data(angle_inputs, results):
    """将输入和结果保存到JSON文件中。"""
    data = {
        "angle_inputs": angle_inputs,
        "results": results
    }
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        messagebox.showerror("保存错误", f"无法保存数据: {str(e)}")

def load_data():
    """从JSON文件中加载输入和结果数据。如果文件不存在，返回默认值。"""
    if not os.path.exists(DATA_FILE):
        return None, None
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("angle_inputs", None), data.get("results", None)
    except Exception as e:
        messagebox.showerror("读取错误", f"无法读取数据文件: {str(e)}")
        return None, None

def on_calculate():
    """GUI计算按钮的回调函数。"""
    angle_inputs = [
        entry1.get(),
        entry2.get(),
        entry3.get(),
        entry4.get(),
        entry5.get()
    ]

    try:
        results = calculate_results(angle_inputs)
    except ValueError as ve:
        messagebox.showerror("输入错误", str(ve))
        return
    except ZeroDivisionError as zde:
        messagebox.showerror("计算错误", str(zde))
        return
    except Exception as e:
        messagebox.showerror("错误", f"发生错误: {str(e)}")
        return

    # 构建输出字符串
    output = (
        f"平均角度 Φ̄ = {results['Phi_bar_deg']}°{results['Phi_bar_min']:.2f}′\n"
        f"角度标准差 S_Φ = {results['S_phi_deg']}°{results['S_phi_min']:.2f}′\n"
        f"总不确定度 Δ_Φ = {results['Delta_phi_rad']:.6f} rad\n"
        f"平均距离 d̄ = {results['d_bar_mm']:.6f} mm\n"
        f"距离不确定度 Δ_d = {results['Delta_d_mm']:.6f} mm\n"
        f"相对不确定度 E_d = {results['E_d_percent']:.2f}%\n"
        f"最终结果 d = {results['d_bar_mm']:.6f} mm ± {results['Delta_d_mm']:.6f} mm"
    )

    # 显示结果
    result_label.config(text=output)

    # 保存数据到文件
    save_data(angle_inputs, results)

def on_clear():
    """清除输入框和结果，并删除存储的文件。"""
    # 清除输入框
    entry1.delete(0, tk.END)
    entry2.delete(0, tk.END)
    entry3.delete(0, tk.END)
    entry4.delete(0, tk.END)
    entry5.delete(0, tk.END)

    # 清除结果显示
    result_label.config(text="")

    # 删除数据文件
    if os.path.exists(DATA_FILE):
        try:
            os.remove(DATA_FILE)
        except Exception as e:
            messagebox.showerror("删除错误", f"无法删除数据文件: {str(e)}")

def populate_fields(angle_inputs, results):
    """将加载的数据填充到输入框和结果显示中。"""
    if angle_inputs:
        entry1.delete(0, tk.END)
        entry1.insert(0, angle_inputs[0])

        entry2.delete(0, tk.END)
        entry2.insert(0, angle_inputs[1])

        entry3.delete(0, tk.END)
        entry3.insert(0, angle_inputs[2])

        entry4.delete(0, tk.END)
        entry4.insert(0, angle_inputs[3])

        entry5.delete(0, tk.END)
        entry5.insert(0, angle_inputs[4])

    if results:
        output = (
            f"平均角度 Φ̄ = {results['Phi_bar_deg']}°{results['Phi_bar_min']:.2f}′\n"
            f"角度标准差 S_Φ = {results['S_phi_deg']}°{results['S_phi_min']:.2f}′\n"
            f"总不确定度 Δ_Φ = {results['Delta_phi_rad']:.6f} rad\n"
            f"平均距离 d̄ = {results['d_bar_mm']:.6f} mm\n"
            f"距离不确定度 Δ_d = {results['Delta_d_mm']:.6f} mm\n"
            f"相对不确定度 E_d = {results['E_d_percent']:.2f}%\n"
            f"最终结果 d = {results['d_bar_mm']:.6f} mm ± {results['Delta_d_mm']:.6f} mm"
        )
        result_label.config(text=output)

# 创建GUI窗口
root = tk.Tk()
root.title("分光计计算器")

# 设置窗口大小
root.geometry("500x700")

# 创建并放置输入标签和文本框
tk.Label(root, text="请输入五组角度（格式：度°分′，可带小数）：", font=("Arial", 12)).pack(pady=10)

frame = tk.Frame(root)
frame.pack(pady=5)

# 创建五组输入
entry1 = tk.Entry(frame, width=15, font=("Arial", 12))
entry1.grid(row=0, column=0, padx=5, pady=5)
entry1.insert(0, "30°15.5′")

entry2 = tk.Entry(frame, width=15, font=("Arial", 12))
entry2.grid(row=1, column=0, padx=5, pady=5)
entry2.insert(0, "30°10.2′")

entry3 = tk.Entry(frame, width=15, font=("Arial", 12))
entry3.grid(row=2, column=0, padx=5, pady=5)
entry3.insert(0, "30°20.7′")

entry4 = tk.Entry(frame, width=15, font=("Arial", 12))
entry4.grid(row=3, column=0, padx=5, pady=5)
entry4.insert(0, "30°15.3′")

entry5 = tk.Entry(frame, width=15, font=("Arial", 12))
entry5.grid(row=4, column=0, padx=5, pady=5)
entry5.insert(0, "30°18.4′")

# 创建计算按钮
calc_button = tk.Button(root, text="计算", command=on_calculate, font=("Arial", 12))
calc_button.pack(pady=10)

# 创建清除按钮
clear_button = tk.Button(root, text="清除", command=on_clear, font=("Arial", 12), fg="red")
clear_button.pack(pady=5)

# 创建结果显示标签
result_label = tk.Label(root, text="", justify="left", font=("Arial", 12))
result_label.pack(pady=10)

# 加载之前保存的数据（如果有）
loaded_angle_inputs, loaded_results = load_data()
populate_fields(loaded_angle_inputs, loaded_results)

# 运行GUI主循环
root.mainloop()
