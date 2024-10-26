import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import HeaderBox from './headerBox.jsx';
import { Bar, Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);
const Dashboard = () => {
  const dummyImageData = [
    { id: 1, name: 'Image 1', flocs: [{ id: 1, size: 10 }, { id: 2, size: 15 }] },
    { id: 2, name: 'Image 2', flocs: [{ id: 3, size: 8 }, { id: 4, size: 12 }, { id: 5, size: 7 }] },
    { id: 3, name: 'Image 3', flocs: [{ id: 6, size: 20 }] },
    { id: 4, name: 'Image 4', flocs: [{ id: 7, size: 5 }, { id: 8, size: 9 }, { id: 9, size: 11 }, { id: 10, size: 6 }] },
  ];
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
    fetchLatestImagesData(); // Fetch data when component mounts
    prepareChartData(dummyImageData, null);
  }, []);

  const prepareChartData = (data, flocSumData) => {
    const labels = data.map(image => image.name);
    const flocCounts = data.map(image => image.flocs.length);
    const avgFlocSizes = data.map(image => 
      image.flocs.reduce((sum, floc) => sum + floc.size, 0) / image.flocs.length
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
          tension: 0.1
        },
        {
          label: 'Sum of Floc Areas',
          data: flocSumData,
          fill: false,
          borderColor: 'rgb(54, 162, 235)',
          tension: 0.1
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
      const imagesResponse = await fetch('http://127.0.0.1:5000/images/');
      const imagesData = await imagesResponse.json();
      setLatestImagesData(imagesData);
  
      const flocSumResponse = await fetch('http://127.0.0.1:5000/images/floc_sum', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ limit: 10 }) // Adjust the limit as needed
      });
      const flocSumData = await flocSumResponse.json();
      setFlocSumData(flocSumData.sum_floc_areas);
  
      prepareChartData(imagesData, flocSumData.sum_floc_areas);
    } catch (error) {
      console.error('Error fetching data:', error);
    }
  };

  return (
    <div>
      <HeaderBox currentTab={0}/>
      <div className="contentContainer" style={{textAlign: 'center', overflowY:'scroll' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <h1>Dashboard</h1>
          <img className="dashboardIcon" src="https://png.pngtree.com/png-vector/20230302/ourmid/pngtree-dashboard-line-icon-vector-png-image_6626604.png" alt="" width="50px" height="50px"></img>
        </div>
        <p style={{marginTop:'-5px'}}>New Floc Images and Data</p>

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
          {/* Render the latest images data */}
          {latestImagesData.map((image, index) => (
            <div className="imageWrapper" key={index} style={{ display: 'inline-block', margin: '10px' }}>
              <img src={`data:image/jpeg;base64,${image.image}`} alt={`Image ${index}`} />
              <div className="image-data">
                <p>ID: {image.id}  |  Name: {image.name}</p>
                <p style={{marginBottom: "0px"}}>Floc data: {image.flocs.map((floc, idx) => (
                    <li key={idx}>ID: {floc.id}, Size: {floc.size}</li>
                  ))}</p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}

export default Dashboard;