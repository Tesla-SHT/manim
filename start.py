from manim import *

class First_scene(Scene):
    def construct(self):
        t = Text("This is the first scene")
        self.play(Write(t))
        self.wait(2)



class ConvolutionAnimation(Scene):
    def construct(self):
        # 创建输入图像矩阵
        input_matrix = IntegerMatrix(
            [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            left_bracket="(",
            right_bracket=")",
        ).shift(LEFT * 2)

        # 创建卷积核
        kernel_matrix = IntegerMatrix(
            [[-1, 0], [1, 2]],
            left_bracket="(",
            right_bracket=")",
        ).shift(RIGHT * 2)

        # 创建卷积后的结果
        result_matrix = IntegerMatrix(
            [[10, 20], [30, 40]],
            left_bracket="(",
            right_bracket=")",
        ).shift(DOWN * 2)

        # 标注
        input_label = Text("Input Image").next_to(input_matrix, UP)
        kernel_label = Text("Kernel").next_to(kernel_matrix, UP)
        result_label = Text("Result").next_to(result_matrix, UP)

        # 动画展示
        self.play(Write(input_matrix), Write(input_label))
        self.play(Write(kernel_matrix), Write(kernel_label))
        self.wait()

        # 卷积滑动过程
        sliding_kernel = kernel_matrix.copy()
        for i in range(2):
            for j in range(2):
                self.play(sliding_kernel.animate.move_to(input_matrix.get_entries()[(i + 1) * 3 + j + 1].get_center()))
                self.wait(0.5)

        self.play(Write(result_matrix), Write(result_label))
        self.wait()
