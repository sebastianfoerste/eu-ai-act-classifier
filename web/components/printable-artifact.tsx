import type { PrintDocument } from "../lib/print";

// What goes to paper or PDF (ADR 0003, part 1). A table is used for layout only:
// browsers repeat a table's header group at the top of every printed page, so the
// draft notice opens page 1 and every page after it, without `@page` margin boxes.
export function PrintableArtifact({ doc }: { doc: PrintDocument }) {
  return (
    <section className="printOnly" aria-label="Printable draft artifact">
      <table className="printSheet" role="presentation">
        <thead>
          <tr>
            <td>
              <p className="printNotice">{doc.notice}</p>
            </td>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>
              <pre>{doc.content}</pre>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
