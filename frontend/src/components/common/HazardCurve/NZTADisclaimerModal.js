import React from "react";

import Box from "@material-ui/core/Box";
import Typography from "@material-ui/core/Typography";
import Modal from "@material-ui/core/Modal";

const style = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  border: "2px solid #000",
  boxShadow: 24,
  p: 4,
};

const NZTADisclaimerModal = ({ status, setStatus }) => {
  return (
    <div>
      <Modal
        open={status}
        onClose={() => setStatus(false)}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={style}>
          <Typography id="modal-modal-title" variant="h6" component="h2">
            Reference
          </Typography>
          <Typography id="modal-modal-description" sx={{ mt: 2 }}>
            Conversion from Larger to RotD50 are done based on Boore et al.
            (2017), Some Horizontal-Component Ground-Motion Intensity Measures
            Used in Practice
          </Typography>
        </Box>
      </Modal>
    </div>
  );
};

export default NZTADisclaimerModal;
