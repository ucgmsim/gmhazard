import React, { Fragment, useState, useEffect } from "react";

import "assets/style/Messages.css";

const GuideMessage = ({ header, body, instruction }) => {
  const [instructions, setInstructions] = useState([]);
  const [JSXVs30, setJSXVs30] = useState([
    <Fragment key="vs30">
      V<sub>S30</sub>
    </Fragment>,
  ]);

  useEffect(() => {
    if (instruction) {
      setInstructions(instruction);
    }
  }, [instruction]);

  return (
    <div className="card text-black bg-warning mb-3 card-message">
      <div className="card-header">{header === "VS30" ? JSXVs30 : header}</div>
      <div className="card-body">
        <h5 className="card-title">{body}</h5>
        <ol>
          {instructions.map((value, index) => {
            return <li key={index}>{value}</li>;
          })}
        </ol>
      </div>
    </div>
  );
};

export default GuideMessage;
