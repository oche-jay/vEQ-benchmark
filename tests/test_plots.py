'''
Created on 22 May 2015

@author: ooe
'''
import unittest
import plotter


class Test(unittest.TestCase):
    def setUp(self):
        self.bitrate = [439170, 718299, 65216, 208674, 1763657, 441, 3608806, 413, 1462860, 299603, 1898446, 2103923, 192, 3701694, 6780, 4077543, 664, 476, 2224582, 98371]
        self.cpus= [0.0, 5.9, 5.5, 4.0, 40.6, 23.9, 24.5, 26.4, 27.9, 29.5, 37.1, 31.4, 32.0, 35.8, 34.1, 32.5, 38.0, 30.9, 26.4, 30.0, 38.4]
        self.powers = [74.6, 71.3, 71.8, 81.0, 75.0, 75.0, 75.9, 75.2, 73.9, 95.1, 84.1, 71.4, 74.6, 74.0, 72.8, 71.8, 74.2, 82.7, 79.3, 74.2, 73.2, 72.4, 77.3, 77.6, 74.1, 89.3, 78.4, 74.7, 76.9, 73.6, 78.3, 96.9, 117.2, 117.7, 106.4, 87.6, 81.9, 89.3, 79.0, 86.0, 78.2, 95.1, 87.6, 93.2, 90.6, 90.2, 80.8, 94.6, 81.1, 73.7, 75.0, 78.1, 78.0, 74.9, 77.0, 72.4, 73.3]
        self.memorys= [0.37056302993121365, 0.3953039205458501, 0.395973886635995, 0.3960935234378066, 0.3967156348072268, 0.3971941820144732, 0.397553092419908, 0.3980794943478789, 0.3990365887623717, 0.9046456405785062, 0.9218254853186503, 0.9218733400393749, 0.9219929768411865, 0.9222561778051719, 0.9222561778051719, 0.9222561778051719, 0.9222561778051719, 0.9341720032656061, 0.9344352042295917, 0.9344352042295917, 0.9344352042295917, 0.9344830589503164, 0.9344830589503164, 0.9272569961208963, 0.9492940950145908, 0.9492940950145908, 0.9494615865371271, 0.9502272620687212, 0.9502272620687212, 0.9441497125366926, 0.9494615865371271, 0.9539120755645182, 0.9539120755645182, 0.9539120755645182, 0.9539120755645182, 0.9461117560864027, 0.9526439254653154, 0.9530028358707501, 0.9559698285556775, 0.9581711457090106, 0.9589846759613295, 0.9589846759613295, 0.9589846759613295, 0.9543906227717647, 0.9544624048528514, 0.9620234507273439, 0.9620234507273439, 0.9620234507273439, 0.9577165258621267, 0.9577643805828514, 0.9577643805828514, 0.9577883079432137, 0.964822951889735, 0.964822951889735, 0.9603246081416195, 0.9607553006281411, 0.960970646871402, 0.9554434266277065, 0.9555869907898804, 0.957285833375605, 0.9606595911866918]


    def tearDown(self):
        pass


    def testplotter(self):
#         plt.plot(self.bitrate)
#         plt.show()
#         plotter.plot(self.cpu)
        pass
        plotter.plot(self.powers, title="Power Usage")

    def testsubplots(self):
        title = "Codec Info" + "- Moviename"
        plotter.makeSubPlot(start_time=123456,figure_title=title, cpus=self.cpus,memorys=self.memorys,powers=self.powers,bitrate=self.bitrate)


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()