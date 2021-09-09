import React from "react";

import { Modal, ModalHeader, ModalBody } from "reactstrap";

import "assets/style/Modal.css";

const ModalComponent = ({ modal, setModal, title, body }) => {
  const toggle = () => setModal(!modal);

  return (
    <Modal isOpen={modal} toggle={toggle}>
      <ModalHeader toggle={toggle}>{title}</ModalHeader>
      <ModalBody className="msg-wrapper">{body}</ModalBody>
    </Modal>
  );
};

export default ModalComponent;
