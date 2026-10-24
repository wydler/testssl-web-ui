#!/usr/bin/env python3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from flask import Flask, Response, request, render_template, flash, stream_with_context

try:
    from markupsafe import escape
except ImportError:
    from flask import escape

import os
from os import urandom
import selectors
import signal
import subprocess
import time
import re
import socket
import ipaddress

SENTINEL = '------------SPLIT----------HERE---------'

application = Flask(__name__)

### Configuration ###
checkCmd = "/opt/testssl.sh/testssl.sh"
checkArgs = ["--quiet"]
checkTimeout = int(os.environ.get("CHECKTIMEOUT", default=300))
testsslDebug = int(os.environ.get("TESTSSLDEBUG", default=0))
rendererCmd = "aha"
rendererArgs = ["-n"]
rendererTimeout = 30
protocols = ["ftp", "smtp", "pop3", "imap", "xmpp", "telnet", "ldap"]
scantypes = ["certonly", "normal", "full"]
reHost = re.compile(r"^[a-zA-Z0-9_][a-zA-Z0-9_\-]+(\.[a-zA-Z0-9_\-]+)*$")
preflightRequest = True
preflightTimeout = 10
application.secret_key = os.environ.get("SECRET_KEY") or urandom(32)
#####################


def terminate_process(process):
    if process is None:
        return

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass

    if process.poll() is None:
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass

    if process.poll() is None:
        process.wait()


def render_line(line):
    renderer = None
    try:
        renderer = subprocess.Popen(
            [rendererCmd, *rendererArgs],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        html, err = renderer.communicate(input=line, timeout=rendererTimeout)
    except OSError as error:
        return None, f"Unable to start HTML formatter: {error}"
    except subprocess.TimeoutExpired:
        terminate_process(renderer)
        _, err = renderer.communicate()
        message = "HTML formatting timed out"
        if err:
            message += ": " + err.decode("utf-8", errors="replace")
        return None, message
    finally:
        terminate_process(renderer)

    if renderer.returncode != 0:
        message = f"HTML formatting failed with error code {renderer.returncode}"
        if err:
            message += ": " + err.decode("utf-8", errors="replace")
        return None, message

    return html, None


@application.route("/", methods=['GET', 'POST'])
def main():
    if request.method == 'GET':
        return render_template("main.html", form=request.form)

    invalid = False
    host = request.form.get('host', '').strip()
    if not reHost.fullmatch(host):
        flash("Wrong host name!")
        invalid = True

    if host == "localhost" or host.startswith("127.") or host == "::1":
        flash("I was already pentested ;)")
        invalid = True

    target_ip = request.form.get('ip', '').strip()
    if target_ip:
        try:
            parsed_ip = ipaddress.ip_address(target_ip)
            if parsed_ip.is_loopback or (
                isinstance(parsed_ip, ipaddress.IPv6Address)
                and parsed_ip.ipv4_mapped is not None
                and parsed_ip.ipv4_mapped.is_loopback
            ):
                flash("Loopback IP addresses are not allowed!")
                invalid = True
        except ValueError:
            flash("Wrong IP address!")
            invalid = True

    try:
        port = int(request.form.get('port', ''))
    except ValueError:
        flash("Port number must be numeric")
        port = None
        invalid = True

    if port is not None and not 0 <= port <= 65535:
        flash("Wrong port number!")
        port = None
        invalid = True

    scantype = request.form.get('scantype', '')
    if scantype not in scantypes:
        flash("Wrong scantype!")
        invalid = True

    starttls = request.form.get('starttls') == "yes"
    protocol = request.form.get('protocol', '')
    if starttls and protocol not in protocols:
        flash("Wrong protocol!")
        invalid = True

    if request.form.get('confirm') != "yes":
        flash("You must confirm that you are authorized to scan the given system!")
        invalid = True

    if invalid:
        return render_template("main.html", form=request.form)

    if preflightRequest:
        try:
            with socket.create_connection((target_ip or host, port), timeout=preflightTimeout):
                pass
        except OSError:
            flash("Connection failed!")
            return render_template("main.html", form=request.form)

    testssl_args = [checkCmd, *checkArgs, "--debug=" + str(testsslDebug)]
    if target_ip:
        testssl_args.extend(["--ip", target_ip, "--nodns", "none"])

    if scantype == "normal":
        testssl_args.append("--ids-friendly")
    elif scantype == "certonly":
        testssl_args.append("--server-defaults")

    if starttls:
        testssl_args.extend(["-t", protocol])
    testssl_args.append(host + ":" + str(port))

    def runtest():
        first, _, last = render_template('result.html', result=SENTINEL).partition(SENTINEL)
        yield first
        check = None
        selector = selectors.DefaultSelector()
        stderr_output = bytearray()
        stderr_limit = 65536
        stderr_truncated = False
        pending_line = bytearray()
        timed_out = False
        deadline = time.monotonic() + checkTimeout

        try:
            try:
                check = subprocess.Popen(
                    testssl_args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                )
            except OSError as error:
                yield f"<pre>{escape(f'Unable to start testssl.sh: {error}')}</pre>"
                yield last
                return

            selector.register(check.stdout, selectors.EVENT_READ, "stdout")
            selector.register(check.stderr, selectors.EVENT_READ, "stderr")

            while selector.get_map():
                if not timed_out and time.monotonic() >= deadline:
                    timed_out = True
                    terminate_process(check)

                timeout = None if timed_out else max(0, deadline - time.monotonic())
                for key, _ in selector.select(timeout):
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        key.fileobj.close()
                        continue

                    if key.data == "stderr":
                        remaining = stderr_limit - len(stderr_output)
                        if remaining > 0:
                            stderr_output.extend(chunk[:remaining])
                        if len(chunk) > remaining:
                            stderr_truncated = True
                        continue

                    pending_line.extend(chunk)
                    while b'\n' in pending_line:
                        line, _, rest = pending_line.partition(b'\n')
                        pending_line = bytearray(rest)
                        html, error = render_line(line + b'\n')
                        if error:
                            yield f"<pre>{escape(error)}</pre>"
                            terminate_process(check)
                            yield last
                            return
                        yield html.decode("utf-8", errors="replace")

            if pending_line:
                html, error = render_line(pending_line)
                if error:
                    yield f"<pre>{escape(error)}</pre>"
                    terminate_process(check)
                    yield last
                    return
                yield html.decode("utf-8", errors="replace")

            try:
                returncode = check.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
                terminate_process(check)
                returncode = check.wait()

            if timed_out:
                yield f"<pre>{escape(f'Test timed out after {checkTimeout} seconds.')}</pre>"
            elif returncode != 0:
                error = stderr_output.decode("utf-8", errors="replace").strip()
                if stderr_truncated:
                    error += "\n[stderr output truncated]"
                if not error:
                    error = f"testssl.sh exited with status {returncode}"
                yield f"<pre>{escape(error)}</pre>"

            yield last
        finally:
            selector.close()
            terminate_process(check)
            if check is not None:
                for stream in (check.stdout, check.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()

    return Response(stream_with_context(runtest()), mimetype='text/html')

@application.route("/about/")
def about():
    check = subprocess.run(
        [checkCmd, "--version"],
        capture_output=True,
        check=True,
        timeout=checkTimeout,
    )

    try:
        with open("/opt/testssl.sh/git-log.txt", "rb") as changelog_file:
            changelog = changelog_file.read()
    except IOError as e:
        changelog = b"\n\n[Error reading changelog: %s]" % str(e).encode('utf-8')

    # Append changelog to output
    full_output = check.stdout + b"\nCommit log testssl.sh:\n\n" + changelog
    renderer = subprocess.run(
        [rendererCmd, *rendererArgs],
        input=full_output,
        capture_output=True,
        check=True,
        timeout=rendererTimeout,
    )
    return render_template(
        "about.html",
        about=renderer.stdout.decode("utf-8", errors="replace"),
    )

if __name__ == "__main__":
    application.run(host='0.0.0.0')
