功能：在一次淹没模拟后，接收一个(x, y)坐标对，根据这个坐标对找到对应网格开始淹没的时刻，然后找到对应时刻的佛子岭、磨子潭、白莲崖坝下水位返回

思路：

1. 通过Flask服务器监听POST请求（api_coord.py）
2. 如何判断上一次模拟已经正确结束？——server.log
   `192.168.2.148 - - [09/Jan/2025 11:09:00] "POST /set_2d_hydrodynamic_data HTTP/1.1" 200 -`
   要求最后包含`"POST /set_2d_hydrodynamic_data HTTP/1.1" 200 -`
3. 根据坐标对在shp网格文件（可以用`max_water_area.shp`）中查找对应的网格，在其属性表中读取网格的编号
4. 根据网格编号对应`output.csv`中的一列数据，查找该列数据从0变为任意值的对应行索引
5. 分别选取位于3个坝下的网格，根据第4步中的行索引和网格的编号（列索引）查找对应单元格的值，即为需要的坝下水位
6. 最后，把这3个值return回去

设计：

CoordHandler类，构造方法接受config.RESULT_PATH赋给self.result_path，包含：

* check_finish方法，检测上一次模拟是否正常结束
* find_grid_id(x, y)方法，根据坐标对在`max_water_area.shp`查找对应的网格，在其属性表中读取网格的编号fid并返回
* find_flooding(fid)方法，根据fid查找对应列数据0变为任意值的对应行索引row_index并返回
* find_dam_water_depth(row_index)方法，根据row_index查找3个坝下网格对应的水位值并返回
