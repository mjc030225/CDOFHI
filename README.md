# V1.0 已实现功能

## 1 登录以及注册界面的完善。

可以使用人脸检测的方式去进行登录，在注册的时候，可以仅仅录入姓名密码即可，如录入了人脸信息，那就可以密码登录和人脸识别登录选一个即可。

信息均保存在本地。

# 2 基本的识别任务

识别任务包括语音 人脸 以及手势识别指令。

# 3 与模拟平台的连接

模拟平台包括sitl_jmavsim以及sitl_gazebo,相关的配置可以在后文见到。

连接功能包括，实时更新当前drone的状态，包括电量，三个方向的速度。

以及起飞降落功能。

控制部分，实现了对于模拟飞行器的基本控制，包括四个维度，高度油门，三个欧拉角的控制实现对飞行器的控制。

### 后续部分

打算解决gazebo模拟平台的深度相机功能，实时传输相关拍摄场景到本地qt平台上显现。但是这可能会很吃硬件。因为gazebo平台本身需要硬件有很强的渲染能力，本人目前设备可能并不支持。

最后考虑移入到实际的无人机设备上。

# 本篇仅仅讨论在两个不同平台上安装不同仿真环境的步骤以及踩坑

## 1 Jmavsim PX4 on windows

用windows配置jmavsim有两种方式，第一种wsl2。这个反而复杂了。其实px4的环境相对在ubuntu上还算好配，后续放弃的原因在于，之前的代码不适用linux环境下的流式摄像头，故放弃。

也可以通过虚拟机看到。LINUX 用的是V4L2（VIDEO FOR LINUX）摄像头，这种摄像头的处理逻辑和windows不同，你会发现在windows上可用的opencv代码完全不受用，同时最大的痛苦还是在于ubuntu下opencv-python和pyqt5版本的冲突，当时忙了好几天的no plugin问题。

![](C:\Users\admin\Desktop\CDOFHI\1717342283711.png)


也就是这个问题，后续需要各种调试不同版本的pyqt5版本才勉强解决了显示问题，但是V4L2 摄像头的问题，直到现在也没弄懂。最后放弃了。

我选择的使用cygwin这样的一个工具链去配置jmavsim，成效就是虽然没有摄像头，但是已经能够基本完成飞行，解锁等等功能。效果如下图所示。

![](C:\Users\admin\Desktop\CDOFHI\1717342689396.png)

可用mavsdk去控制jmavsim的起飞降落，以及返回各种数据。

配置过程大致如下：

### 1.1 配置cygwin

cygwin是一个非常不错好用的unix平台，可以在windows上运行，但是他的配置过程比用虚拟机还是要复杂的多，毕竟只是unix和linux还是有很多不同的地方。

从使用角度来看：Cygwin就是一个Windows软件，该软件就是在Windows上仿真Linux操作系统。简而言之，Cygwin是一个在Windows平台上运行的 Linux模拟环境，使用一个Dll(动态链接库)来实现，这样，我们可以开发出Cygwin下的UNIX工具，使用这个DLL运行在Windows下，可以想一下，在运行Windows的同时，也可以使用VI，BASH，TAR，SED等UNIX下的工具，这个VM虚拟机有很相同的原理，但是VM是虚拟多个，而Cygwin是同时使用Windows和UNIX，这样对于那些在Windows和Unix下移植的程序来说是比较简单的事情了。

在官网下载**cygwin**

[Cygwin Installation](https://cygwin.com/install.html)

然后安装一些依赖包：

![](C:\Users\admin\Desktop\CDOFHI\1717396984776.png)

这些在px4官网上都给出了。python2的找不到就试着用python3的包即可

打开***setup-x86_64.exe***文件下载这些依赖包即可。

然后是其他的依赖

~~~bash
pip install toml
pip install pyserial
pip install pyulog
pip install --user kconfiglib jsonschema future
~~~

注意可能会报错找不到路径，原因是cygwin版本高了，安装的自动是python3，pip3，因此接下来需要：

~~~bash
which pip3
##一般是/usr/bin/pip3
which python3
##一般是usr/bin/python3
which pip #也许会找不到
which python #也许会找不到
ln -s /path/to/pip3 /usr/bin/pip
ln -s /path/to/python3 /usr/bin/python ##软链接
~~~

这样就能bash目录下找到pip了

接下来就是编译源码px4部分：

~~~bash
# Clone the PX4-Autopilot repository into the home folder & loads submodules in parallel
git clone --recursive -j8 https://github.com/PX4/PX4-Autopilot.git
##会很卡 如果这样就不如在本地下下来然后上传到本地cygwin目录下 /path/to/home
cd PX4-Autopilot
# Build and runs SITL simulation with jMAVSim to test the setup
make px4_sitl jmavsim
~~~

cmake的部分是最痛苦的，因为很多错误看了人就非常心烦意乱，完全不知如何从哪里下手，因此要耐心去查询。

我遇到的几个报错，第一是pip包不对，这个最好解决，python版本正确，pip安装就好。

然后是cmake版本低了，那就老老实实更新即可。

复杂一点的是java版本不对，由于jmavsim依托jdk，所以jdk版本会引发大问题。

**安装jdk11**，这个我没找到比较好的解决方案。

只能下载网上的msi直接安装，并且把目录粘贴进去

用软连接连接。

~~~bash
java -version查看版本
~~~



使用mavsdk连接：需要协程编程的一些知识，下面是一个demo：

~~~python
import asyncio
from mavsdk import System

async def run():
    # 创建 MAVSDK System 实例
    drone = System()
    # 连接到 PX4 的 UDP 端口
    await drone.connect(system_address="udp://:14556")

    # 等待连接建立
    print("等待连接...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"连接到车辆 {state.system_id}")
            break

    # 获取飞行器位置
    async for gps_info in drone.telemetry.gps_info():
        print(f"GPS 信息: {gps_info}")
        break

    async for battery in drone.telemetry.battery():
        print(f"电池状态: {battery}")
        break

    async for health in drone.telemetry.health():
        print(f"健康状态: {health}")
        break

    # 使飞行器解锁
    print("-- 解锁飞行器")
    await drone.action.arm()

    # 使飞行器起飞
    print("-- 起飞")
    await drone.action.takeoff()

    await asyncio.sleep(10)

    # 使飞行器降落
    print("-- 降落")
    await drone.action.land()
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run()

~~~

注意使用udp连接，首先需要使用jmavsim

倘若是在同一物理机上，则等待加载后输入

~~~bash
 mavlink start -p -o 14550	#打开remote的udp端口 -p 可选 ip地址 e.g 127.0.0.1
~~~

这样就能将udp本身的14556端口进行广播到14550端口。

# 2 Jmavsim and Gazebo on linux

jmavsim本身不包含深度相机，这表明我们的任务难以圆满完成。所要求的下游任务没法完成，因此我们需要含有深度相机的仿真，例如gazebo。

注意：这里使用ubuntu 20.04 LTS作为示例，其余版本可能有所差别。

首先和



