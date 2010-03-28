# --with NomachineKey
# Allow login with the key shipped with the NoMachine client.
# This can be a security risk, so it is disabled by default
# and an SSH key is generated at install time.
%bcond_with NomachineKey

Summary:        Free NX implementation
Name:           freenx
Version:        0.7.3
Release:        %mkrel 5
License:        GPLv2
Group:          Networking/Remote access
URL:            http://freenx.berlios.de/
Source0:        http://download.berlios.de/freenx/freenx-server-%{version}.tar.gz
Source1:        freenx-nxserver.logrotate
Patch0:         freenx-nxsetup-warning.patch
Patch2:         freenx-0.7.3-nxagent_3.3.0.patch
# add patch from CentOS to use the init script to make sure /tmp/.X11-unix exists
# otherwise freenx fails to work, also the init script cleans out dead NX sessions
Patch3:         freenx-0.7.2-initd-script.patch
Requires:       expect
Requires:       netcat
Requires:       nxagent
Requires:       nxproxy
Requires:       openssh-server
Requires:       Xdialog
Requires:       xmessage
Requires:       xterm
Requires(pre):  rpm-helper
Requires(post): expect
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root

%description
NoMachine NX is the next-generation X compression and roundtrip 
suppression scheme. It can operate remote X11 sessions over 56k 
modem dialup links or anything better.

This package contains a free (GPL) implementation of the nxserver
component.
 
%prep
%setup -q -n %{name}-server-%{version}
%patch2 -p1 -b .nxagent_version
%patch3 -p1 -b .init

%build
perl -pi -e "s|/var/lib/nxserver/home|%{_localstatedir}/lib/nxserver/nxhome|" nxloadconfig
pushd nxserver-helper
%make
popd

# README.install.urpmi doesn't work yet.
cat << EOF > README.urpmi
After installing this package, an nx user is created (this is a 
system user, do not try to log in as him), with a home located 
at %{_localstatedir}/lib/nxserver/nxhome. His password is a random 
32-character password. 

%if %with NomachineKey
Using Nomachine ssh key, warning, this is a potential security risk.
%else
Your user must install the key located at: 
%{_localstatedir}/lib/nxserver/nxhome/.ssh/client.id_dsa.key
to log in.

For knx, put it in: %{_datadir}/knx/ with world-readable right.
For nomachine.com Nx client for windows put it in : C:\Program
Files\NX Client for Windows\share

You user will now be able to log in using their username 
and password provided you have ssh logins enabled for them
%endif
EOF

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_sbindir}
install -m 755 {nxdialog,nxkeygen,nxloadconfig,nxnode,nxnode-login,nxserver,nxserver-helper/nxserver-helper} %{buildroot}%{_bindir}
install -m 755 nxsetup %{buildroot}%{_sbindir}

mkdir -p %{buildroot}%{_localstatedir}/lib/nxserver/nxhome/.ssh
mkdir -p %{buildroot}%{_localstatedir}/lib/nxserver/db/{closed,failed,running}
mkdir -p %{buildroot}%{_sysconfdir}/nxserver
mkdir -p %{buildroot}%{_logdir}
/bin/touch %{buildroot}%{_sysconfdir}/nxserver/{passwords,passwords.orig,users.id_dsa,users.id_dsa.pub}
/bin/touch %{buildroot}%{_localstatedir}/lib/nxserver/nxhome/.ssh/{server.id_dsa.pub.key,client.id_dsa.key,authorized_keys2,known_hosts}
/bin/touch %{buildroot}%{_logdir}/nxserver.log
install node.conf.sample %{buildroot}%{_sysconfdir}/nxserver/node.conf
#/bin/echo 'ENABLE_1_5_0_BACKEND="1"' >> %{buildroot}%{_sysconfdir}/nxserver/node.conf
/bin/echo 'ENABLE_2_0_0_BACKEND="1"' >> %{buildroot}%{_sysconfdir}/nxserver/node.conf
/bin/echo 'ENABLE_ROOTLESS_MODE="1"' >> %{buildroot}%{_sysconfdir}/nxserver/node.conf
mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
cp -a %{SOURCE1} %{buildroot}%{_sysconfdir}/logrotate.d/%{name}

# install init script
install -D -m 755 init.d/freenx-server %{buildroot}%{_initrddir}/freenx-server

# tell spec-helper to not remove passwords.orig
export DONT_CLEANUP=1

%clean
rm -rf %{buildroot}

%pre
if [ $1 = 1 ]; then
        %_pre_useradd nx %{_localstatedir}/lib/nxserver/nxhome %{_bindir}/nxserver
fi

%postun
if [ $1 = 0 ]; then
        %_postun_userdel nx
fi

%post
%_post_service freenx-server

# make a link from %{_usr}/X11R6/lib/X11/fonts -> %{_datadir}/fonts if needed
[ ! -d %{_usr}/X11R6/lib/X11/fonts ] && %{__ln_s} %{_datadir}/fonts %{_usr}/X11R6/lib/X11/ 
if [ $1 = 1 ]; then
        %{_bindir}/ssh-keygen -f %{_sysconfdir}/nxserver/users.id_dsa -t dsa -N "" 2>&1 > /dev/null
        chown nx.root %{_sysconfdir}/nxserver/users.id_dsa 
        chmod 600 %{_sysconfdir}/nxserver/users.id_dsa

%if %with NomachineKey
        cat << EOF > %{_localstatedir}/lib/nxserver/nxhome/.ssh/authorized_keys2
ssh-dss AAAAB3NzaC1kc3MAAACBAJe/0DNBePG9dYLWq7cJ0SqyRf1iiZN/IbzrmBvgPTZnBa5FT/0Lcj39sRYt1paAlhchwUmwwIiSZaON5JnJOZ6jKkjWIuJ9MdTGfdvtY1aLwDMpxUVoGwEaKWOyin02IPWYSkDQb6cceuG9NfPulS9iuytdx0zIzqvGqfvudtufAAAAFQCwosRXR2QA8OSgFWSO6+kGrRJKiwAAAIEAjgvVNAYWSrnFD+cghyJbyx60AAjKtxZ0r/Pn9k94Qt2rvQoMnGgt/zU0v/y4hzg+g3JNEmO1PdHh/wDPVOxlZ6Hb5F4IQnENaAZ9uTZiFGqhBO1c8Wwjiq/MFZy3jZaidarLJvVs8EeT4mZcWxwm7nIVD4lRU2wQ2lj4aTPcepMAAACANlgcCuA4wrC+3Cic9CFkqiwO/Rn1vk8dvGuEQqFJ6f6LVfPfRTfaQU7TGVLk2CzY4dasrwxJ1f6FsT8DHTNGnxELPKRuLstGrFY/PR7KeafeFZDf+fJ3mbX5nxrld3wi5titTnX+8s4IKv29HJguPvOK/SI7cjzA+SqNfD7qEo8= root@nettuno
EOF
%else
        %{_bindir}/ssh-keygen -q -t dsa -N '' -f %{_localstatedir}/lib/nxserver/nxhome/.ssh/local.id_dsa 2>&1 > /dev/null
        mv -f %{_localstatedir}/lib/nxserver/nxhome/.ssh/local.id_dsa %{_localstatedir}/lib/nxserver/nxhome/.ssh/client.id_dsa.key
        mv -f %{_localstatedir}/lib/nxserver/nxhome/.ssh/local.id_dsa.pub %{_localstatedir}/lib/nxserver/nxhome/.ssh/server.id_dsa.pub.key
        cat %{_localstatedir}/lib/nxserver/nxhome/.ssh/server.id_dsa.pub.key >  %{_localstatedir}/lib/nxserver/nxhome/.ssh/authorized_keys2
        
%endif
        /bin/echo -n "127.0.0.1 " > %{_localstatedir}/lib/nxserver/nxhome/.ssh/known_hosts
        cat %{_sysconfdir}/ssh/ssh_host_rsa_key.pub >> %{_localstatedir}/lib/nxserver/nxhome/.ssh/known_hosts
        chmod 600 %{_localstatedir}/lib/nxserver/nxhome/.ssh/*
        chown nx.root %{_localstatedir}/lib/nxserver/nxhome/.ssh/*
        %create_ghostfile %{_sysconfdir}/nxserver/users.id_dsa.pub root root 644
        %create_ghostfile %{_sysconfdir}/nxserver/passwords.orig nx root 600
        %create_ghostfile %{_sysconfdir}/nxserver/passwords nx root 600
        %create_ghostfile %{_logdir}/nxserver.log nx root 600
        %{_bindir}/mkpasswd -l 32 | %{_bindir}/passwd --stdin nx 2>&1 > /dev/null
fi

%preun
%_preun_service freenx-server

%files
%defattr(0644,root,root,0755)
%doc AUTHORS README.urpmi
%attr(0755,root,root) %{_bindir}/nxdialog
%attr(0755,root,root) %{_bindir}/nxkeygen
%attr(0755,root,root) %{_bindir}/nxloadconfig
%attr(0755,root,root) %{_bindir}/nxnode
%attr(0755,root,root) %{_bindir}/nxnode-login
%attr(0755,root,root) %{_bindir}/nxserver
%attr(0755,root,root) %{_bindir}/nxserver-helper
%attr(0755,root,root) %{_sbindir}/nxsetup
%config(noreplace) %{_sysconfdir}/logrotate.d/%{name}
%attr(0755,root,root) %{_initrddir}/freenx-server
%attr(755,nx,root) %dir %{_sysconfdir}/nxserver
%attr(755,nx,root) %dir %{_localstatedir}/lib/nxserver
%attr(755,nx,root) %dir %{_localstatedir}/lib/nxserver/db
%attr(700,nx,root) %dir %{_localstatedir}/lib/nxserver/db/closed
%attr(700,nx,root) %dir %{_localstatedir}/lib/nxserver/db/failed
%attr(700,nx,root) %dir %{_localstatedir}/lib/nxserver/db/running
%attr(755,nx,root) %dir %{_localstatedir}/lib/nxserver/nxhome
%attr(700,nx,root) %dir %{_localstatedir}/lib/nxserver/nxhome/.ssh
%attr(644,nx,root) %config(noreplace) %{_sysconfdir}/nxserver/node.conf
%attr(600,nx,root) %ghost %{_sysconfdir}/nxserver/passwords
%attr(600,nx,root) %ghost %{_sysconfdir}/nxserver/users.id_dsa
%attr(644,root,root) %ghost %{_sysconfdir}/nxserver/users.id_dsa.pub
%attr(600,nx,root) %ghost %{_sysconfdir}/nxserver/passwords.orig
%attr(600,nx,root) %ghost %{_localstatedir}/lib/nxserver/nxhome/.ssh/known_hosts
%attr(600,nx,root) %ghost %{_localstatedir}/lib/nxserver/nxhome/.ssh/authorized_keys2
%attr(600,nx,root) %ghost %{_localstatedir}/lib/nxserver/nxhome/.ssh/client.id_dsa.key
%attr(600,nx,root) %ghost %{_localstatedir}/lib/nxserver/nxhome/.ssh/server.id_dsa.pub.key
# E: freenx non-root-user-log-file /var/log/nxserver.log nx
%attr(600,nx,root) %ghost %{_logdir}/nxserver.log
