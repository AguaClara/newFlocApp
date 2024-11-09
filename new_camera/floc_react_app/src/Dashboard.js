import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import HeaderBox from './headerBox.jsx';
import { Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

const Dashboard = () => {
  const [flocSumData, setFlocSumData] = useState([]);
  const [latestImagesData, setLatestImagesData] = useState([]);
  const [barChartData, setBarChartData] = useState({
    labels: [],
    datasets: [],
  });
  const [lineChartData, setLineChartData] = useState({
    labels: [],
    datasets: [],
  });

  useEffect(() => {
    fetchLatestImagesData();
  }, []);

  const prepareChartData = (data, flocSumData) => {
    const labels = data.map((image) => image.name);

    // Handle cases where `flocs` might be empty
    const flocCounts = data.map((image) => image.flocs.length || 0);
    const avgFlocSizes = data.map((image) =>
      image.flocs.length > 0
        ? image.flocs.reduce((sum, floc) => sum + floc.size, 0) / image.flocs.length
        : 0
    );

    setBarChartData({
      labels: labels,
      datasets: [
        {
          label: 'Number of Flocs',
          data: flocCounts,
          backgroundColor: 'rgba(75, 192, 192, 0.6)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1,
        },
      ],
    });

    setLineChartData({
      labels: labels,
      datasets: [
        {
          label: 'Average Floc Size',
          data: avgFlocSizes,
          fill: false,
          borderColor: 'rgb(255, 99, 132)',
          tension: 0.1,
        },
        {
          label: 'Sum of Floc Areas',
          data: flocSumData,
          fill: false,
          borderColor: 'rgb(54, 162, 235)',
          tension: 0.1,
        },
      ],
    });
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
      },
    },
  };

  const fetchLatestImagesData = async () => {
    try {
      // Fetch the images data
      const imagesResponse = await fetch('http://127.0.0.1:5000/images/');
      const imagesData = await imagesResponse.json();

      // Fetch the sum of floc areas
      const flocSumResponse = await fetch('http://127.0.0.1:5000/images/floc_sum', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      const flocSumData = await flocSumResponse.json();

      // Update state with fetched data
      setLatestImagesData(imagesData);
      setFlocSumData(flocSumData.sum_floc_areas);

      // Prepare the chart data using the fetched data
      prepareChartData(imagesData, flocSumData.sum_floc_areas);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  return (
    <div>
      <HeaderBox currentTab={0} />
      <div className="contentContainer" style={{ textAlign: 'center', overflowY: 'scroll' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <h1>Dashboard</h1>
          <img
            className="dashboardIcon"
            src="https://png.pngtree.com/png-vector/20230302/ourmid/pngtree-dashboard-line-icon-vector-png-image_6626604.png"
            alt=""
            width="50px"
            height="50px"
          />
        </div>
        <p style={{ marginTop: '-5px' }}>New Floc Images and Data</p>

        <div className="dashboardBoxWrapper" style={{ overflowX: 'scroll', whiteSpace: 'nowrap' }}>
          {/* Chart.js Bar Chart */}
          <div style={{ width: '80%', margin: '20px auto' }}>
            <h2>Floc Count per Image</h2>
            <Bar data={barChartData} options={chartOptions} />
          </div>

          {/* Chart.js Line Chart */}
          <div style={{ width: '80%', margin: '20px auto' }}>
            <h2>Average Floc Size per Image</h2>
            <Line data={lineChartData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
