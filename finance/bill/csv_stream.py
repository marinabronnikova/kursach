import codecs
import csv

from django.http import HttpResponse


class CSVStream:
    """Class to stream (download) an iterator to a
    CSV file."""
    def export(self, filename, fieldnames,  iterator):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={filename}.csv"'
        writer = csv.writer(response)
        writer.writerow(fieldnames)

        for data in iterator:
            writer.writerow(data)

        response.write(codecs.BOM_UTF8)
        return response
