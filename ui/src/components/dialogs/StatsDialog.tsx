import React from "react";
import { Modal } from "../Modal/Modal";

type StatsDialogProps = {
  reviewedToday: number;
  avgReviewSec: number;
  queueDepth: number;
  slaCompliancePct: number;
  onClose: () => void;
};

export function StatsDialog({ reviewedToday, avgReviewSec, queueDepth, slaCompliancePct, onClose }: StatsDialogProps) {
  return (
    <Modal
      aria-labelledby="stats-title"
      titleId="stats-title"
      title="Stats"
      onClose={onClose}
    >
      <p>Items reviewed today: {reviewedToday}</p>
      <p>Average review time: {avgReviewSec}s</p>
      <p>Queue depth: {queueDepth}</p>
      <p>SLA compliance: {slaCompliancePct}%</p>
    </Modal>
  );
}
