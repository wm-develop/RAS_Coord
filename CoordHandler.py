# -*- coding: utf-8 -*-
# @Time    : 2025/2/27 下午8:34
# @Author  : wm
# @Software   : PyCharm
import os
import pandas as pd
from osgeo import ogr, osr


class CoordHandler:
    def __init__(self, result_path):
        self.source_srs = None
        self.target_srs = None
        self.result_path = result_path
        self.shapefile_path = os.path.join(self.result_path, 'demo2/demo2.shp')
        self.output_csv = pd.read_csv(os.path.join(self.result_path, 'output.csv'), header=None)
        self.geometries = []  # 存储几何对象和FID
        self.fid_index = {}

    def read_shapefile(self):
        """
        读取shp文件，提取所有features的GeometryRef和FID，记录在self.geometries中
        :return:
        """
        ds = ogr.Open(self.shapefile_path)
        if ds is None:
            raise RuntimeError("无法打开shp文件")
        layer = ds.GetLayer()

        # 提取FID
        for feature in layer:
            geom = feature.GetGeometryRef().Clone()
            fid = feature.GetFID()
            self.geometries.append((geom, fid))
            self.fid_index[fid] = len(self.geometries) - 1

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

    def find_grid_id(self, fid):
        """
        根据FID在`max_water_area.shp`查找对应的网格，在其属性表中读取网格的编号fid并返回
        :param fid: 验证过的合法FID（整数）
        :return: 网格的编号fid
        """
        if fid not in self.fid_index:
            raise ValueError(f"编号为 {fid} 的网格未找到")
        return fid

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
        根据row_index查找3个坝下网格对应的水位值并返回
        佛子岭：17367
        白莲崖：25497
        磨子潭：24832
        :param row_index: 淹没开始时刻对应的行索引值
        :return: 3个坝下网格对应的水位值
        """
        dam_fids = [17367, 25497, 24832]
        # 检查row_index是否合法
        if row_index >= len(self.output_csv) or row_index < 0:
            raise AssertionError("时间步不合法")

        try:
            values = []
            for fid in dam_fids:
                # 获取对应fid列的数据，然后取row_index行的值
                value = self.output_csv[fid].iloc[row_index]
                values.append(value)
            # 返回佛子岭、白莲崖、磨子潭水深组成的三元组
            return tuple(values)
        except KeyError as e:
            raise IndexError(f"FID {e} 不存在于结果文件中")
