import React from "react";

import RingLoader from "react-spinners/RingLoader";
import Center from "react-center";

class LoadingSpinner extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      loading: true,
    };
  }

  render() {
    return (
      <Center>
        {/* I used inline style as its only one attribute and I didn't think it was worth creating another css file just for this */}
        <div className="sweet-loading" style={{ marginTop: "20%" }}>
          <RingLoader
            size={100}
            color={"#123abc"}
            loading={this.state.loading}
          />
        </div>
      </Center>
    );
  }
}

export default LoadingSpinner;
