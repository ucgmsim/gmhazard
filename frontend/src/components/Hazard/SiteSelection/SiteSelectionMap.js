import React, { useState, useEffect, useContext } from "react";

import ReactMapGL, { Marker, NavigationControl } from "react-map-gl";

import { GlobalContext } from "context";

import { SiteSelectionMapPin } from "components/Hazard/SiteSelection";
import {
  MAP_BOX_WIDTH,
  MAP_BOX_HEIGHT,
  MAP_BOX_TOKEN,
} from "constants/Constants";

import "assets/style/SiteSelectionMap.css";

const SiteSelectionMap = () => {
  const { mapBoxCoordinate, setMapBoxCoordinate } = useContext(GlobalContext);

  const [viewport, setViewport] = useState({
    latitude: Number(mapBoxCoordinate.lat),
    longitude: Number(mapBoxCoordinate.lng),
    zoom: 14,
  });

  useEffect(() => {
    setViewport({
      latitude: Number(mapBoxCoordinate.lat),
      longitude: Number(mapBoxCoordinate.lng),
      zoom: 14,
    });
  }, [mapBoxCoordinate]);

  const addPinToMap = (event) => {
    setMapBoxCoordinate({
      lat: event.lngLat[1],
      lng: event.lngLat[0],
      input: "MapBox",
    });
  };

  return (
    <ReactMapGL
      {...viewport}
      width={MAP_BOX_WIDTH}
      height={MAP_BOX_HEIGHT}
      mapboxApiAccessToken={MAP_BOX_TOKEN}
      onViewportChange={(nextViewport) => {
        setViewport(nextViewport);
      }}
      mapStyle="mapbox://styles/mapbox/streets-v9"
      onClick={(e) => addPinToMap(e)}
    >
      <div className="navi-control">
        <NavigationControl />
      </div>
      <Marker
        latitude={Number(mapBoxCoordinate.lat)}
        longitude={Number(mapBoxCoordinate.lng)}
        offsetTop={-20}
        offsetLeft={-10}
      >
        <SiteSelectionMapPin size={25} />
      </Marker>
    </ReactMapGL>
  );
};

export default SiteSelectionMap;
