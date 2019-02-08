# --with NomachineKey
# Allow login with the key shipped with the NoMachine client.
# This can be a security risk, so it is disabled by default
# and an SSH key is generated at install time.
%bcond_with NomachineKey

%define debug_package %{nil}

Summary:        Free NX implementation
Name:           freenx
Version:        0.7.3
Release:        12
License:        GPLv2
Group:          Networking/Remote access
URL:            http://freenx.berlios.de/
Source0:        http://download.berlios.de/freenx/freenx-server-%{version}.tar.gz
Source1:        freenx-nxserver.logrotate
Patch0:         freenx-server-0.7.3-lp-fixes.patch
Patch1:         freenx-server-r104-fixes.patch
Patch2:		freenx-server-0.7.3-connection-fix.patch
Patch3:		freenx-server-0.7.3-authkeys2.patch
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

%description
NoMachine NX is the next-generation X compression and roundtrip 
suppression scheme. It can operate remote X11 sessions over 56k 
modem dialup links or anything better.

This package contains a free (GPL) implementation of the nxserver
component.
 
%prep
%setup -q -n %{name}-server-%{version}
%patch0 -p1 -b .lp
%patch1 -p1 -b .fixes
%patch2 -p0 -b .connection-fix
%patch3 -p1 -b .authkeys2

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
/bin/touch %{buildroot}%{_localstatedir}/lib/nxserver/nxhome/.ssh/{server.id_dsa.pub.key,client.id_dsa.key,authorized_keys,known_hosts}
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
        cat << EOF > %{_localstatedir}/lib/nxserver/nxhome/.ssh/authorized_keys
ssh-dss AAAAB3NzaC1kc3MAAACBAJe/0DNBePG9dYLWq7cJ0SqyRf1iiZN/IbzrmBvgPTZnBa5FT/0Lcj39sRYt1paAlhchwUmwwIiSZaON5JnJOZ6jKkjWIuJ9MdTGfdvtY1aLwDMpxUVoGwEaKWOyin02IPWYSkDQb6cceuG9NfPulS9iuytdx0zIzqvGqfvudtufAAAAFQCwosRXR2QA8OSgFWSO6+kGrRJKiwAAAIEAjgvVNAYWSrnFD+cghyJbyx60AAjKtxZ0r/Pn9k94Qt2rvQoMnGgt/zU0v/y4hzg+g3JNEmO1PdHh/wDPVOxlZ6Hb5F4IQnENaAZ9uTZiFGqhBO1c8Wwjiq/MFZy3jZaidarLJvVs8EeT4mZcWxwm7nIVD4lRU2wQ2lj4aTPcepMAAACANlgcCuA4wrC+3Cic9CFkqiwO/Rn1vk8dvGuEQqFJ6f6LVfPfRTfaQU7TGVLk2CzY4dasrwxJ1f6FsT8DHTNGnxELPKRuLstGrFY/PR7KeafeFZDf+fJ3mbX5nxrld3wi5titTnX+8s4IKv29HJguPvOK/SI7cjzA+SqNfD7qEo8= root@nettuno
EOF
%else
        %{_bindir}/ssh-keygen -q -t dsa -N '' -f %{_localstatedir}/lib/nxserver/nxhome/.ssh/local.id_dsa 2>&1 > /dev/null
        mv -f %{_localstatedir}/lib/nxserver/nxhome/.ssh/local.id_dsa %{_localstatedir}/lib/nxserver/nxhome/.ssh/client.id_dsa.key
        mv -f %{_localstatedir}/lib/nxserver/nxhome/.ssh/local.id_dsa.pub %{_localstatedir}/lib/nxserver/nxhome/.ssh/server.id_dsa.pub.key
        cat %{_localstatedir}/lib/nxserver/nxhome/.ssh/server.id_dsa.pub.key >  %{_localstatedir}/lib/nxserver/nxhome/.ssh/authorized_keys
        
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
%attr(600,nx,root) %ghost %{_localstatedir}/lib/nxserver/nxhome/.ssh/authorized_keys
%attr(600,nx,root) %ghost %{_localstatedir}/lib/nxserver/nxhome/.ssh/client.id_dsa.key
%attr(600,nx,root) %ghost %{_localstatedir}/lib/nxserver/nxhome/.ssh/server.id_dsa.pub.key
# E: freenx non-root-user-log-file /var/log/nxserver.log nx
%attr(600,nx,root) %ghost %{_logdir}/nxserver.log


%changelog
* Mon Feb 28 2011 Funda Wang <fwang@mandriva.org> 0.7.3-10mdv2011.0
+ Revision: 640868
- rebuild

* Mon Feb 14 2011 Lev Givon <lev@mandriva.org> 0.7.3-9
+ Revision: 637651
- Patch nxserver connection problem (#61008).

* Mon Feb 14 2011 Lev Givon <lev@mandriva.org> 0.7.3-8
+ Revision: 637644
- Correct path to nxloadconfig (#61530).
  Use su instead of runuser in init script.

* Sun Dec 05 2010 Oden Eriksson <oeriksson@mandriva.com> 0.7.3-7mdv2011.0
+ Revision: 610766
- rebuild

* Tue Jun 01 2010 Ahmad Samir <ahmadsamir@mandriva.org> 0.7.3-6mdv2010.1
+ Revision: 546825
- drop patche0, it's old and doesn't apply anyway
- add two patches from Fedora, should fix (mdv#59579) and (mdv#59572)
- drop patches 2,3 as they're part of the Fedora patches now
- renumber the patches

* Sun Mar 28 2010 Ahmad Samir <ahmadsamir@mandriva.org> 0.7.3-5mdv2010.1
+ Revision: 528539
- really sync sources
- clean spec
- add patch from CentOS to use the init script to make sure /tmp/.X11-unix
  exists otherwise freenx fails to work, also the init script cleans out dead
  NX sessions (fixes mdv bug#51240)

* Mon Nov 30 2009 Ahmad Samir <ahmadsamir@mandriva.org> 0.7.3-4mdv2010.1
+ Revision: 471959
- Remove ENABLE_1_5_0_BACKEND="1" (fix bug #51242)

* Fri Sep 11 2009 Thierry Vignaud <tv@mandriva.org> 0.7.3-3mdv2010.0
+ Revision: 437593
- rebuild

* Tue Dec 16 2008 Adam Williamson <awilliamson@mandriva.org> 0.7.3-2mdv2009.1
+ Revision: 314711
- package is no longer noarch, nxserver-helper is a binary
- build and install nxserver-helper: needed for slave mode to work, which
  seems to be upstream's preferred method now

* Tue Dec 09 2008 Adam Williamson <awilliamson@mandriva.org> 0.7.3-1mdv2009.1
+ Revision: 312057
- update nxagent version patch for 3.3.0
- drop removeunix-sockets.patch (merged upstream)
- drop 0.7.1-0.7.2-405-417.patch (superseded by 0.7.3)
- new license policy
- new release 0.7.3

* Thu Jul 24 2008 Thierry Vignaud <tv@mandriva.org> 0.7.1-7mdv2009.0
+ Revision: 245399
- rebuild

  + Pixel <pixel@mandriva.com>
    - adapt to %%_localstatedir now being /var instead of /var/lib (#22312)

* Thu Jan 31 2008 Emmanuel Blindauer <blindauer@mandriva.org> 0.7.1-5mdv2008.1
+ Revision: 160624
- fixed typo

* Mon Jan 28 2008 Emmanuel Blindauer <blindauer@mandriva.org> 0.7.1-4mdv2008.1
+ Revision: 159077
- fix patch
- BS: fix the patch and make what I say!
- removed 0.7.0 source
- fix typo
- removed typo
- update patch  for 3.1.0
- really patch for 3.1.0

* Sun Jan 27 2008 Emmanuel Blindauer <blindauer@mandriva.org> 0.7.1-2mdv2008.1
+ Revision: 158781
- readd patch
- remove patch ?!
- dont forget to bump release
- added patch for nx-3.1.0
  added patch for testing unix sockets (Yves-Gael Cheny)

* Sun Jan 27 2008 Emmanuel Blindauer <blindauer@mandriva.org> 0.7.1-1mdv2008.1
+ Revision: 158691
- bumped to 0.7.2 (0.7.1 + svn upgrade)
  removed patch0 (merged uptream)

  + Olivier Blin <oblin@mandriva.com>
    - restore BuildRoot

  + Thierry Vignaud <tv@mandriva.org>
    - kill re-definition of %%buildroot on Pixel's request

* Thu Sep 06 2007 Jérôme Soyer <saispo@mandriva.org> 0.7.0-1mdv2008.0
+ Revision: 80702
- New release 0.7.0

* Mon Aug 20 2007 Emmanuel Blindauer <blindauer@mandriva.org> 0.6.0-3mdv2008.0
+ Revision: 67230
+ rebuild (emptylog)

* Mon Aug 20 2007 Emmanuel Blindauer <blindauer@mandriva.org> 0.6.0-2mdv2008.0
+ Revision: 67215
- really fix the missing link. REALLY!


* Wed Mar 14 2007 Emmanuel Blindauer <blindauer@mandriva.org> 0.6.0-2mdv2007.1
+ Revision: 143892
- don't forget to increase release
- remove the link fonts from package
- Fixes creation of /usr/X11R6/lib/X11/fonts if not available

  + David Walluck <walluck@mandriva.org>
    - update sources
    - 0.6.0
      macros
      use macros for paths
      create users.id_dsa.pub ghostfile
      use %%bcond_with
      some grammar fixes
      bunzip2 souces and patches and use more consistent names
      use more explicit file list

* Thu Jan 04 2007 Crispin Boylan <crisb@mandriva.org> 0.5.0-3.rev281.3mdv2007.1
+ Revision: 103936
- Fix typo in Requires

* Wed Jan 03 2007 Crispin Boylan <crisb@mandriva.org> 0.5.0-3.rev281.2mdv2007.1
+ Revision: 103901
- Actually bump revision

* Wed Jan 03 2007 Crispin Boylan <crisb@mandriva.org> 0.5.0-3.rev281.1mdv2007.1
+ Revision: 103891
- Fix Requires (#26321)
- Import freenx

* Thu Sep 21 2006 Emmanuel Blindauer <blindauer@mandriva.org> 0.5.0-3.rev281.1mdv2007.0
- upgrade to svn 281 to be compatible with nx-2.0.0 and nxclient v2
- enable NX 2.0.0 backend
- add link for fonts to support /usr/share/fonts

* Sun Jul 30 2006 Couriousous <couriousous@mandriva.org> 0.5.0-2mdv2007.0
- Add expect to requires(post)

* Thu Jul 13 2006 Couriousous <couriousous@mandriva.org> 0.5.0-1mdv2007.0
- 0.5.0

* Mon Aug 08 2005 Couriousous <couriousous@mandriva.org> 0.4.4-1mdk
- 0.4.4

* Sun Jul 31 2005 Couriousous <couriousous@mandriva.org> 0.4.3-2mdk
- Enable NX 1.5.0 backend

* Sat Jul 30 2005 Couriousous <couriousous@mandriva.org> 0.4.3-1mdk
- 0.4.3

* Sun Jul 24 2005 Couriousous <couriousous@mandriva.org> 0.4.2-1mdk
- 0.4.2 ( Bugfix )

* Wed Jun 29 2005 Couriousous <couriousous@mandriva.org> 0.4.1-1mdk
- 0.4.1 ( Bugfix )

* Fri May 13 2005 Emmanuel Blindauer <blindauer@mandriva.org> 0.4.0-2mdk
- Rebuild for the right /var/lib

* Thu May 12 2005 Emmanuel Blindauer <blindauer@mandriva.org> 0.4.0-1mdk
- 0.4 release
- Rediff P1

* Fri Apr 01 2005 Couriousous <couriousous@mandrake.org> 0.3.1-2mdk
- Package nxclient binary ( fix #15140 )

* Tue Mar 22 2005 Couriousous <couriousous@mandrake.org> 0.3.1-1mdk
- Final 0.3.1

* Sat Mar 12 2005 Couriousous <couriousous@mandrake.org> 0.3.1-0.pre1.1mdk
- Add bugfixes from upstream ( == 0.3.1-pre1 )

* Thu Mar 10 2005 Emmanuel Blindauer <mdk@agat.net> 0.3.0-3mdk
- Really fix permissions, only users in root group were able to log.

* Thu Mar 10 2005 Emmanuel Blindauer <mdk@agat.net> 0.3.0-2mdk
- Fix permissions on node.conf (or no-one can log in)

* Sun Mar 06 2005 Couriousous <couriousous@mandrake.org> 0.3.0-1mdk
- 0.3.0
- Some spec tweak

* Wed Feb 23 2005 Couriousous <couriousous@mandrake.org> 0.2.8-2mdk
- Try to fix bug #13670

* Fri Feb 11 2005 Couriousous <couriousous@mandrake.org> 0.2.8-1mdk
- 0.2.8

* Sat Dec 25 2004 Couriousous <couriousous@mandrake.org> 0.2.7-2mdk
- Better README.urpmi from Matthew Roller

* Fri Dec 03 2004 couriousous <couriousous@zarb.org> 0.2.7-1mdk
- First Mandrakelinux release
- Automatic setup
- Set nx home as /var/lib/nxserver/nxhome

