from manim import *
class bayesindependent(Scene):
    def construct(self):
        partitions = [[0, 2], [1]]
        inactive1 = DiGraph(
            layout="partite",
            partitions=partitions,
            labels = True,
            vertices=[0, 1, 2],
            edges=[(0, 1), (1, 2)],
            vertex_config={
                0: {"fill_color": WHITE},
                1: {"fill_color": GRAY},
                2: {"fill_color": WHITE}
            },
            edge_config={
                (0,1): {"stroke_color": WHITE},
                (1,2): {"stroke_color": WHITE}
            }

        )
        inactive1.shift(LEFT,LEFT,LEFT,LEFT)
        self.play(Create(inactive1))

        inactive2 = DiGraph(
            layout="partite",
            partitions=partitions,
            labels = True,
            vertices=[0, 1, 2],
            edges=[(1,2), (1, 0)],
            vertex_config={
                0: {"fill_color": WHITE},
                1: {"fill_color": GRAY},
                2: {"fill_color": WHITE}
            },
            edge_config={
                (1,2): {"stroke_color": WHITE},
                (1,0): {"stroke_color": WHITE}
            }
        )
        self.play(Create(inactive2))
        #self.play(inactive2.animate.shift(LEFT,LEFT,LEFT,LEFT))

        inactive3 = DiGraph(
            layout="partite",
            partitions=partitions,
            labels = True,
            vertices=[0, 1, 2],
            edges=[(0,1), (2,1)],
            vertex_config={
                0: {"fill_color": WHITE},
                1: {"fill_color": WHITE},
                2: {"fill_color": WHITE}
            },
            edge_config={
                (0,1): {"stroke_color": WHITE},
                (2,1): {"stroke_color": WHITE}
            })
        inactive3.shift(RIGHT*4)
        self.play(Create(inactive3))
        t2 = Tex("inactive")
        t2.shift(UP*3)
        t2.set_color(RED)
        self.play(FadeIn(t2))
        #move it to the top
        self.wait(1)
        self.play(FadeOut(inactive1), FadeOut(inactive2), FadeOut(inactive3))
        self.play(Unwrite(t2))


        t = Text("active")
        t.set_color(GREEN)
        t.shift(UP*3)
        self.play(Write(t))

        active1 = DiGraph(
            layout="partite",
            partitions=partitions,
            labels = True,
            vertices=[0, 1, 2],
            edges=[(0, 1), (1, 2)],
            vertex_config={
                0: {"fill_color": WHITE},
                1: {"fill_color": WHITE},
                2: {"fill_color": WHITE}
            },
            edge_config={
                (0,1): {"stroke_color": WHITE},
                (1,2): {"stroke_color": WHITE}
            }
        )
        active1.shift(LEFT*5)
        self.play(Create(active1))

        active2 = DiGraph(
            layout="partite",
            partitions=partitions,
            labels = True,
            vertices=[0, 1, 2],
            edges=[(1,2), (1, 0)],
            vertex_config={
                0: {"fill_color": WHITE},
                1: {"fill_color": WHITE},
                2: {"fill_color": WHITE}
            },
            edge_config={
                (1,2): {"stroke_color": WHITE},
                (1,0): {"stroke_color": WHITE}
            }
        )
        active2.shift(LEFT*2)
        self.play(Create(active2))

        active3 = DiGraph(
            layout="partite",
            partitions=partitions,
            labels = True,
            vertices=[0, 1, 2],
            edges=[(0,1), (2,1)],
            vertex_config={
                0: {"fill_color": WHITE},
                1: {"fill_color": GRAY},
                2: {"fill_color": WHITE}
            },
            edge_config={
                (0,1): {"stroke_color": WHITE},
                (2,1): {"stroke_color": WHITE}
            }
        )
        self.play(Create(active3))

        partitionactive =[ [0,2],[1],[3]]
        active4 = DiGraph(
            layout="partite",
            partitions=partitionactive,
            labels = True,
            vertices=[0, 1, 2, 3],
            edges=[(0,1), (2,1), (1,3)],
            vertex_config={
                0: {"fill_color": WHITE},
                1: {"fill_color": WHITE},
                2: {"fill_color": WHITE},
                3: {"fill_color": GRAY}
            },
            edge_config={
                (0,1): {"stroke_color": WHITE},
                (2,1): {"stroke_color": WHITE},
                (1,3): {"stroke_color": WHITE}
            }
        )
        active4.shift(RIGHT*4)
        self.play(Create(active4))

        self.play(Unwrite(t2))
        self.wait(1)
        self.play( FadeOut(active1), FadeOut(active2), FadeOut(active3),FadeOut(active4))

        





