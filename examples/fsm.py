from transitions import Machine

# 1️⃣ 定义咖啡机的状态
states = ["idle", "brewing", "dispensing", "cleaning", "off"]


# 2️⃣ 创建咖啡机类
class CoffeeMachine:
    def __init__(self):
        # 绑定状态机
        self.machine = Machine(model=self, states=states, initial="idle")

        # 3️⃣ 添加状态转换规则
        self.machine.add_transition(trigger="start_brewing", source="idle", dest="brewing", before="heat_water")
        self.machine.add_transition(trigger="finish_brewing", source="brewing", dest="dispensing", after="pour_coffee")
        self.machine.add_transition(trigger="finish_dispensing", source="dispensing", dest="cleaning",
                                    after="auto_clean")
        self.machine.add_transition(trigger="finish_cleaning", source="cleaning", dest="idle")

        # 任何状态 → off
        self.machine.add_transition(trigger="power_off", source="*", dest="off")
        # off → idle
        self.machine.add_transition(trigger="power_on", source="off", dest="idle")

    # 4️⃣ 定义咖啡机操作
    def heat_water(self):
        print("🔵 Heating water...")

    def pour_coffee(self):
        print("☕ Pouring coffee into the cup...")

    def auto_clean(self):
        print("🧼 Automatically cleaning the machine...")

if __name__ == "__main__":

    # 5️⃣ 创建咖啡机对象
    coffee_machine = CoffeeMachine()

    # 6️⃣ 运行状态机
    print(f"Current state: {coffee_machine.state}")  # idle
    coffee_machine.start_brewing()  # 触发 brewing
    print(f"Current state: {coffee_machine.state}")  # brewing
    coffee_machine.finish_brewing()  # 触发 dispensing
    print(f"Current state: {coffee_machine.state}")  # dispensing
    coffee_machine.finish_dispensing()  # 触发 cleaning
    print(f"Current state: {coffee_machine.state}")  # cleaning
    coffee_machine.finish_cleaning()  # 触发 idle
    print(f"Current state: {coffee_machine.state}")  # idle

    # 关闭电源
    coffee_machine.power_off()
    print(f"Current state: {coffee_machine.state}")  # off

    # 重新开机
    coffee_machine.power_on()
    print(f"Current state: {coffee_machine.state}")  # idle
