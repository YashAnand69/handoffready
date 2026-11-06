const stages = [
  ['01 / RECEIVE','Received does not mean approved.','A Switch-managed agent stages the actual attachment bytes. The local lead previews the changes and explicitly confirms the complete packet before reviewing it.','The agent cannot confirm the packet for you.'],
  ['02 / CLARIFY','Ask what the file is for.','The agent proposes a question linked to the current requirement and file. A reply is recorded with its source and reported speaker; the reviewer checks it before accepting it as context.','A received reply is unverified context, not a delivery assessment.'],
  ['03 / CORRECT','New evidence. Fresh review.','The lead confirms the complete corrected packet. Earlier judgments become stale, while historical records remain unchanged. Retired context does not silently carry into a different packet.','A familiar filename does not prove that the bytes are unchanged.'],
  ['04 / REVIEW','Your decision stays yours.','The reviewer selects the intended files, previews narrow checks, reads the evidence and records an assessment. Private reasoning and public usage notes are separate.','A satisfied assessment cannot erase a failed technical check.'],
  ['05 / RETURN','Freeze once. Verify what returned.','The reviewer previews the public record and exact destination, then authorizes one supervised return. Actual downloaded bytes and the owner’s destination check establish an operator-confirmed result.','An uncertain send stays uncertain. No automatic resend.']
];
const fields=['stage-label','stage-title','stage-copy','stage-boundary'];
document.querySelectorAll('[data-stage]').forEach(button=>button.addEventListener('click',()=>{
  const stage=Number(button.dataset.stage);
  document.querySelectorAll('[data-stage]').forEach(other=>other.setAttribute('aria-pressed',String(other===button)));
  fields.forEach((id,index)=>{document.getElementById(id).textContent=stages[stage][index];});
}));
