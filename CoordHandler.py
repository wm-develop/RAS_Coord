# -*- coding: utf-8 -*-
# @Time    : 2025/2/27 下午8:34
# @Author  : wm
# @Software   : PyCharm
import os
import pandas as pd


class CoordHandler:
    def __init__(self, result_path):
        self.result_path = result_path
        self.output_csv = pd.read_csv(os.path.join(self.result_path, 'output.csv'), header=None)
        self.bailianya_csv = pd.read_csv(os.path.join(self.result_path, 'bailianya.csv'), header=None)
        self.mozitan_csv = pd.read_csv(os.path.join(self.result_path, 'mozitan.csv'), header=None)
        self.foziling_csv = pd.read_csv(os.path.join(self.result_path, 'foziling.csv'), header=None)

    def check_finish(self):
        """
        检测上一次模拟是否正常结束
        :return:
        """
        log_path = os.path.join(self.result_path, 'server.log')
        with open(log_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        last_five = lines[-5:]  # 自动处理行数不足5行的情况
        if not any("最大淹没面积shp文件已保存到" in line for line in last_five):
            raise RuntimeError("上一次淹没模拟未正常完成")

    def find_flooding(self, fid):
        """
        根据fid查找对应列数据0变为任意值的对应行索引row_index并返回
        :param fid: 网格的编号
        :return: 对应行索引row_index
        """
        try:
            # 获取对应fid的列数据
            series = self.output_csv[fid]
        except KeyError:
            raise KeyError("无法根据FID在output.csv中找到对应的列，请检查结果文件的完整性")

        # 遍历所有的时间步
        for i in range(1, len(series)):
            previous = series.iloc[i - 1]
            current = series.iloc[i]
            # 如果前一时刻该网格的水深为0（实际按<=0.005以避免模型计算精度问题）
            if previous <= 0.005 and current > 0:
                return i

        # 如果没找到符合条件的时间步，返回-1
        raise RuntimeError("该FID对应的网格在整个模拟过程中一直被淹没或从未被淹没")

    def find_dam_water_depth(self, row_index):
        """
        根据row_index查找3个坝下网格对应的平均水位值并返回
        bailianya_grids = [25495, 25494, 25496, 25492]
        mozitan_grids = [24834, 24833, 24835, 24832]
        foziling_grids = [24418, 24417, 17369, 17367]
        :param row_index: 淹没开始时刻对应的行索引值
        :return: 3个坝下网格对应的水位值
        """
        # 检查row_index是否合法
        if row_index >= len(self.output_csv) or row_index < 0:
            raise AssertionError("时间步不合法")

        try:
            bailianya_val = self.bailianya_csv.loc[row_index, 0]
            mozitan_val = self.mozitan_csv.loc[row_index, 0]
            foziling_val = self.foziling_csv.loc[row_index, 0]
            # 返回佛子岭、白莲崖、磨子潭水位组成的三元组
            return (bailianya_val, mozitan_val, foziling_val)
        except KeyError as e:
            raise IndexError(f"FID {e.args[0]} 不存在于结果文件中")
