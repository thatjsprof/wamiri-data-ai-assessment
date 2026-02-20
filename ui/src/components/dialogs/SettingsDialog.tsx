import React from "react";
import { Modal } from "../Modal/Modal";

type SettingsDialogProps = {
  onClose: () => void;
};

export function SettingsDialog({ onClose }: SettingsDialogProps) {
  return (
    <Modal
      aria-labelledby="settings-title"
      titleId="settings-title"
      title="Settings"
      onClose={onClose}
    >
      <p>API base and display options can be added here.</p>
    </Modal>
  );
}
